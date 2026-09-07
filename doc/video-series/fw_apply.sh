#!/usr/bin/env bash
# Host-side helper for the "Firewalling the PLC" defense lesson (cybics-19).
#
# The CybICS attack VM has no Docker access, so the iptables rules that restrict
# Modbus (port 502) to authorized hosts are applied by the defender on the ICS
# host - here, directly in the OpenPLC container. Port 502 is left open only to
# the HMI (FUXA) and the process I/O (hwio); every other source is dropped, so
# the plant keeps running while the attack machine is cut off.
#
# Usage: fw_apply.sh apply    # add the rules   (run before rendering / verifying)
#        fw_apply.sh remove   # remove the rules (restore the default open stack)
set -euo pipefail
PLC=virtual-openplc-1
HMI_IP=172.18.0.4      # FUXA
IO_IP=172.18.0.2       # hwio (process I/O)
case "${1:-}" in
  apply)
    docker exec "$PLC" iptables -A INPUT -p tcp --dport 502 -s "$HMI_IP" -j ACCEPT
    docker exec "$PLC" iptables -A INPUT -p tcp --dport 502 -s "$IO_IP" -j ACCEPT
    docker exec "$PLC" iptables -A INPUT -p tcp --dport 502 -j DROP
    echo "firewall applied:"; docker exec "$PLC" iptables -L INPUT -n --line-numbers ;;
  remove)
    docker exec "$PLC" iptables -D INPUT -p tcp --dport 502 -j DROP 2>/dev/null || true
    docker exec "$PLC" iptables -D INPUT -p tcp --dport 502 -s "$IO_IP" -j ACCEPT 2>/dev/null || true
    docker exec "$PLC" iptables -D INPUT -p tcp --dport 502 -s "$HMI_IP" -j ACCEPT 2>/dev/null || true
    echo "firewall removed:"; docker exec "$PLC" iptables -L INPUT -n --line-numbers ;;
  *) echo "usage: $0 apply|remove"; exit 1 ;;
esac
