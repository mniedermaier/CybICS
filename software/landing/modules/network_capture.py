"""
Network packet capture for Sharky, sized for a Raspberry Pi Zero 2 W.

The page shows the newest MAX_PACKETS_IN_MEMORY packets, dissected into
the fields it displays. Every captured frame is also appended to a pcap file
on disk, up to PCAP_MAX_BYTES, so an export holds the whole capture rather
than the ~2 s of lab traffic that fit in the display buffer.

Two things are never left to the client: which interfaces can be captured
(never the uplink to the CTF server) and the BPF filter (always confined to
the lab subnet, built from a fixed list of presets). Both used to come from
the request, and a list or a filter with a closing parenthesis was enough to
capture the event network or the host LAN.
"""
import os
import struct
from array import array
import tempfile
import threading
import time
from collections import deque
from datetime import datetime

from utils.config import (CAPTURE_IDLE_STOP_SECONDS, MAX_PACKETS_IN_MEMORY,
                          PCAP_MAX_BYTES, UPLINK_INTERFACE)
from utils.logger import logger

# Everything Sharky captures is confined to the lab network.
LAB_FILTER = "net 172.18.0.0/24"

# Capture filters a student can pick. The values are BPF; the keys are all
# the request may name, so nothing typed in the browser reaches the compiler.
CAPTURE_FILTERS = {
    '': None,
    'modbus': 'tcp port 502',
    's7comm': 'tcp port 102',
    'opcua': 'tcp port 4840',
    'enip': 'tcp port 44818 or udp port 44818',
    'tcp': 'tcp',
    'udp': 'udp',
    'icmp': 'icmp',
    'arp': 'arp',
}

# Linux ARPHRD_ETHER. The exported pcap declares Ethernet for every frame, so
# an interface of another type (tailscale0, wg0, ppp0, ...) would write
# frames Wireshark cannot read.
_ARPHRD_ETHER = '1'

_NO_OFFSET = 0xFFFFFFFF

# Bytes of transport payload kept per packet for Follow Stream.
_PAYLOAD_PREVIEW = 64


class CaptureError(ValueError):
    """A capture request that names an interface or filter it may not."""


def _is_ethernet(name):
    try:
        with open(f'/sys/class/net/{name}/type', encoding='ascii') as handle:
            return handle.read().strip() == _ARPHRD_ETHER
    except OSError:
        return False


def capturable_interfaces():
    """Every interface a student may capture on, veth ends included."""
    import netifaces

    return [
        name for name in netifaces.interfaces()
        if not name.startswith('lo') and name != UPLINK_INTERFACE and _is_ethernet(name)
    ]


def all_interfaces():
    """The interfaces "All" captures on.

    Scapy reads iface=None as its one default interface (conf.iface, the one
    with the default route), not as every interface, so "All" used to sniff
    the board's Wi-Fi or the host's LAN, where nothing matches the lab
    filter, and captured nothing at all. The veth ends of the containers are
    left out: every packet on one also crosses the lab bridge, so they would
    only show each packet twice.
    """
    return [name for name in capturable_interfaces() if not name.startswith('veth')]


def _check_request(interface, filter_name):
    if not isinstance(interface, str) or not isinstance(filter_name, str):
        raise CaptureError('interface and filter must be strings')
    if filter_name not in CAPTURE_FILTERS:
        raise CaptureError(f"unknown capture filter '{filter_name}'")
    if interface != 'all' and interface not in capturable_interfaces():
        raise CaptureError(f"interface '{interface}' cannot be captured")


class _PcapFile:
    """A pcap file on disk that stops growing at PCAP_MAX_BYTES."""

    def __init__(self):
        handle, self.path = tempfile.mkstemp(prefix='sharky-', suffix='.pcap')
        self.file = os.fdopen(handle, 'wb')
        # Magic, version 2.4, UTC, no accuracy, snap length, Ethernet.
        self.file.write(struct.pack('<IHHiIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1))
        self.size = self.file.tell()
        self.full = False

    def write(self, timestamp, frame):
        """Append a record; return the frame's offset, or None when full."""
        record = 16 + len(frame)
        if self.size + record > PCAP_MAX_BYTES:
            self.full = True
            return None
        seconds = int(timestamp)
        micros = int((timestamp - seconds) * 1_000_000)
        self.file.write(struct.pack('<IIII', seconds, micros, len(frame), len(frame)))
        self.file.write(frame)
        offset = self.size + 16
        self.size += record
        return offset

    def read(self, offset, length):
        self.file.flush()
        with open(self.path, 'rb') as handle:
            handle.seek(offset)
            return handle.read(length)

    def snapshot(self):
        """Flush and return how many bytes are complete records."""
        self.file.flush()
        return self.size

    def close(self):
        try:
            self.file.close()
        finally:
            try:
                os.unlink(self.path)
            except OSError:
                pass


class NetworkCapture:
    """One capture at a time, shown from memory and exported from disk.

    `control` serialises starting and stopping; `lock` guards the captured
    data. They are separate because stopping joins the sniffer thread, and
    that thread takes `lock` for every packet it hands over.
    """

    def __init__(self):
        self.control = threading.Lock()
        self.lock = threading.Lock()
        self.packets = deque(maxlen=MAX_PACKETS_IN_MEMORY)
        self.sniffer = None
        self.pcap = None
        self.packet_id = 0
        # Where packet id n's frame starts in the capture file: offsets[n - 1],
        # NO_OFFSET once the file was full. Four bytes a packet instead of the
        # frame itself, and the hex dump works for any packet in the file,
        # not only the ~2 s still in the display buffer.
        self.offsets = array('I')
        self.error = None
        self.stopped_reason = None
        self.last_poll = 0.0
        logger.info(f"NetworkCapture initialized, showing up to {MAX_PACKETS_IN_MEMORY} packets, "
                    f"exporting up to {PCAP_MAX_BYTES // (1024 * 1024)} MB")

    @property
    def active(self):
        sniffer = self.sniffer
        return sniffer is not None and sniffer.running

    def start(self, interface='all', filter_name=''):
        """Start a capture, ending any that is running. Raises CaptureError."""
        _check_request(interface, filter_name)

        from scapy.all import AsyncSniffer, conf
        from scapy.layers.dns import DNS
        from scapy.layers.inet import ICMP, IP, TCP, UDP
        from scapy.layers.l2 import ARP, Ether

        # Dissect only the layers Sharky shows. Scapy's per-packet cost is
        # mostly dissection, and the lab bridge carries ~600 packets a second.
        # Scapy refuses to filter twice, and the setting is process-wide.
        if not conf.layers.filtered:
            conf.layers.filter([Ether, ARP, IP, TCP, UDP, ICMP, DNS])

        iface = all_interfaces() if interface == 'all' else interface
        bpf = CAPTURE_FILTERS[filter_name]
        bpf = f"({LAB_FILTER}) and ({bpf})" if bpf else LAB_FILTER

        with self.control:
            # The old sniffer is joined before the new one starts: it used to
            # keep running, adding a thread and duplicate packets per restart.
            self._stop_sniffer('restarted')
            with self.lock:
                if self.pcap is not None:
                    self.pcap.close()
                self.packets.clear()
                self.packet_id = 0
                self.offsets = array('I')
                self.error = None
                self.stopped_reason = None
                self.pcap = _PcapFile()
                self.last_poll = time.monotonic()
            sniffer = AsyncSniffer(iface=iface, filter=bpf, prn=self._handle, store=False)
            self.sniffer = sniffer
            sniffer.start()

            # A filter or interface the kernel refuses ends the thread at once.
            time.sleep(0.3)
            if not sniffer.running:
                self.error = str(sniffer.exception or 'capture ended at once')
                self._stop_sniffer('failed')
                raise CaptureError(f'capture could not start: {self.error}')

        threading.Thread(target=self._watch, args=(sniffer,), daemon=True).start()
        logger.info(f"Started capture on {iface}, BPF '{bpf}'")

    def stop(self, reason='stopped'):
        with self.control:
            self._stop_sniffer(reason)

    def _stop_sniffer(self, reason):
        sniffer, self.sniffer = self.sniffer, None
        if sniffer is None:
            return
        try:
            sniffer.stop(join=True)
        except Exception:
            # Not running any more: the thread ended by itself.
            pass
        self.stopped_reason = reason
        logger.info(f"Capture {reason} after {self.packet_id} packets")

    def _watch(self, sniffer):
        """Stop a capture nobody is looking at any more."""
        while self.sniffer is sniffer and sniffer.running:
            time.sleep(5)
            idle = time.monotonic() - self.last_poll
            if self.sniffer is sniffer and idle > CAPTURE_IDLE_STOP_SECONDS:
                logger.info(f"No poll for {CAPTURE_IDLE_STOP_SECONDS} s, stopping the capture")
                with self.control:
                    if self.sniffer is sniffer:
                        self._stop_sniffer('idle')

    def clear(self):
        """Forget the shown packets, and the capture file if nothing is capturing."""
        with self.lock:
            self.packets.clear()
            if not self.active and self.pcap is not None:
                self.pcap.close()
                self.pcap = None
                self.packet_id = 0
                self.offsets = array('I')

    def packets_since(self, since):
        """Packets newer than id `since`, and the capture's state."""
        with self.lock:
            self.last_poll = time.monotonic()
            new = [p for p in self.packets if p['id'] > since]
            return new, self._stats_locked()

    def packet_raw(self, packet_id):
        """A captured frame's bytes, or None if the capture file lacks it."""
        with self.lock:
            if self.pcap is None or not 0 < packet_id <= len(self.offsets):
                return None
            offset = self.offsets[packet_id - 1]
            if offset == _NO_OFFSET:
                return None
            # The record header before the frame says how long it is.
            header = self.pcap.read(offset - 16, 16)
            return self.pcap.read(offset, struct.unpack('<IIII', header)[2])

    def pcap_snapshot(self):
        """(path, size) of the capture file so far, or None."""
        with self.lock:
            if self.pcap is None:
                return None
            return self.pcap.path, self.pcap.snapshot()

    def get_stats(self):
        with self.lock:
            return self._stats_locked()

    def _stats_locked(self):
        return {
            'active': self.active,
            'total_packets': self.packet_id,
            'buffered_packets': len(self.packets),
            # Packets that aged out of the display buffer; the export still has them.
            'dropped_packets': self.packet_id - len(self.packets),
            'max_packets': MAX_PACKETS_IN_MEMORY,
            'pcap_bytes': self.pcap.size if self.pcap else 0,
            'pcap_full': bool(self.pcap and self.pcap.full),
            'error': self.error,
            'stopped_reason': None if self.active else self.stopped_reason,
        }

    def _handle(self, packet):
        try:
            frame = bytes(packet)
            timestamp = float(packet.time)
            data = _dissect(packet)
        except Exception as e:
            logger.error(f"Error processing packet: {e}", exc_info=True)
            return

        with self.lock:
            if self.pcap is None:
                return
            self.packet_id += 1
            # The kernel's receive time, not when Python got round to it.
            ts = datetime.fromtimestamp(timestamp)
            data.update({
                'id': self.packet_id,
                'time': ts.strftime('%H:%M:%S.%f')[:-3],
                'timestamp': ts.isoformat(),
                'length': len(frame),
            })
            self.packets.append(data)
            offset = self.pcap.write(timestamp, frame)
            self.offsets.append(_NO_OFFSET if offset is None else offset)


def _dissect(packet):
    """The fields the page shows, from the layers Scapy dissected."""
    from scapy.layers.dns import DNS
    from scapy.layers.inet import ICMP, IP, TCP, UDP
    from scapy.layers.l2 import ARP, Ether
    from scapy.packet import Raw
    from modules.protocol_parsers import parse_enip, parse_modbus_tcp, parse_opcua, parse_s7comm

    layers = {}
    data = {'source': 'N/A', 'destination': 'N/A', 'protocol': 'OTHER',
            'info': 'Unknown protocol', 'layers': layers}

    if packet.haslayer(Ether):
        eth = packet[Ether]
        layers['ethernet'] = {'src': eth.src, 'dst': eth.dst, 'type': f"0x{eth.type:04x}"}

    if packet.haslayer(ARP):
        arp = packet[ARP]
        data.update(protocol='ARP', source=arp.psrc, destination=arp.pdst,
                    info=f"Who has {arp.pdst}? Tell {arp.psrc}" if arp.op == 1
                    else f"{arp.psrc} is at {arp.hwsrc}")
        return data

    if not packet.haslayer(IP):
        return data

    ip = packet[IP]
    layers['ip'] = {'version': ip.version, 'proto': ip.proto, 'ttl': ip.ttl}
    data.update(source=ip.src, destination=ip.dst, protocol='IP', info=f"Protocol {ip.proto}")
    payload = bytes(packet[Raw].load) if packet.haslayer(Raw) else b''
    if payload:
        data['data'] = payload[:_PAYLOAD_PREVIEW].hex()

    if packet.haslayer(TCP):
        tcp = packet[TCP]
        flags = str(tcp.flags)
        layers['tcp'] = {'sport': tcp.sport, 'dport': tcp.dport, 'flags': flags,
                         'seq': tcp.seq, 'ack': tcp.ack}
        data.update(protocol='TCP', source_port=tcp.sport, dest_port=tcp.dport,
                    info=f"{tcp.sport} → {tcp.dport} [{flags}]")
        if not payload:
            return data
        ports = {tcp.sport, tcp.dport}
        if 502 in ports:
            modbus = parse_modbus_tcp(payload)
            if modbus:
                layers['modbus'] = modbus
                more = f" +{modbus['pdu_count'] - 1} more" if modbus['pdu_count'] > 1 else ''
                data.update(protocol='MODBUS',
                            info=f"Modbus: {modbus['function_name']} (Unit {modbus['unit_id']}){more}")
        elif 102 in ports:
            s7 = parse_s7comm(payload)
            if s7:
                layers['s7comm'] = s7
                if s7.get('protocol_id') == 0x32:
                    data.update(protocol='S7COMM', info=f"S7comm: {s7['message_type_name']}")
                else:
                    data.update(protocol='COTP', info=f"COTP: {s7['message_type_name']}")
        elif 4840 in ports:
            opcua = parse_opcua(payload)
            if opcua:
                layers['opcua'] = opcua
                data.update(protocol='OPCUA',
                            info=f"OPC-UA: {opcua['message_type_name']} ({opcua['chunk_type_name']})")
        elif 44818 in ports:
            enip = parse_enip(payload)
            if enip:
                layers['enip'] = enip
                data.update(protocol='ENIP', info=f"EtherNet/IP: {enip['command_name']}")
    elif packet.haslayer(UDP):
        udp = packet[UDP]
        layers['udp'] = {'sport': udp.sport, 'dport': udp.dport, 'len': udp.len}
        data.update(protocol='UDP', source_port=udp.sport, dest_port=udp.dport,
                    info=f"{udp.sport} → {udp.dport}")
        if packet.haslayer(DNS):
            data.update(protocol='DNS', info="DNS Query/Response")
        elif 44818 in (udp.sport, udp.dport) and payload:
            enip = parse_enip(payload)
            if enip:
                layers['enip'] = enip
                data.update(protocol='ENIP', info=f"EtherNet/IP: {enip['command_name']}")
    elif packet.haslayer(ICMP):
        data.update(protocol='ICMP', info=f"Type {packet[ICMP].type}")

    return data
