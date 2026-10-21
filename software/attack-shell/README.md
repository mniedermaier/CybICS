# CybICS Attack Shell

The attack shell is the attacker host of the lab: a small Alpine container at
**172.18.0.100** inside the plant network, with a terminal in the browser
([ttyd](https://github.com/tsl0922/ttyd)) on port **7681**. The landing page
embeds it under **WebShell → Attack shell**.

It runs in the virtual stack in every mode and on the Raspberry Pi board, where
the [Kali attack machine](../attack-machine/README.md) (about 6 GB) does not
fit. In the virtual stack Kali joins the attack shell's network namespace, so
both are the same host, 172.18.0.100, to the plant, the IDS and the defense
checks.

## Why a container of its own

The landing page's webshell used to be the only terminal on a board. It ran
every command inside the landing container: as root, with host networking and
the Docker socket, and within landing's 64 MB memory limit, so a large scan
could get the dashboard itself OOM-killed. Its commands also reached the plant
from 172.18.0.1, not from the attacker address the IDS and the challenges
expect, and it had no TTY, so nothing interactive worked.

The attack shell has its own memory limit (64 MB on the board; idle it uses
about 3 MB), no Docker socket and no host network. It only holds `NET_RAW` and
`NET_ADMIN`, inside its own network namespace. The landing page keeps its shell
as the **admin shell** for the defense challenges, which need `docker exec`
into the targets.

## What is in it

| | |
|---|---|
| Scanning | nmap with the NSE scripts (`s7-info`, `modbus-discover`, `enip-info`, ...), ping, `nc`, `socat` |
| Web and passwords | curl, wget, ffuf, hydra; wordlists in `/usr/share/wordlists` (nmap's 5000 common passwords) |
| Packets | tcpdump, scapy, iptables |
| Python | pymodbus 3.11.3, asyncua, scapy, python-nmap, colorama, pyserial, requests |
| Training | a copy of `training/` in `/CybICS/training`; `flooding_hpt.py` on the PATH |
| Shell | bash in tmux, vim, nano, less, git, picocom |

`net.ipv4.ip_forward` is on and ICMP redirects are off (set by compose, since
`/proc/sys` is read-only in a container), which is what the ARP
man-in-the-middle in [training/mitm](../../training/mitm/README.md) needs.

## Using it

- Open the landing page, then **WebShell**, or go to `http://<host>:7681`
  directly. Over HTTPS the dashboard uses the proxy's port 17681.
- Every browser tab attaches to the same tmux session, `cybics`. A scan keeps
  running when you switch views, and is still there when you come back.
  `Ctrl-b c` opens another window, `Ctrl-b n` switches between them. Scroll
  with the mouse wheel.
- There is no login, as with the rest of the lab. Anyone who can reach the
  board or the host can use it.

## Limits

- **No passive sniffing.** The plant network is a switched bridge: the
  container's interface only sees its own traffic and broadcasts. To watch the
  plant's traffic, use Sharky on the landing page or capture on the host
  (`br-cybics` on a board). A man-in-the-middle makes traffic pass through
  the shell, which is the point of that challenge.
- **No GUI tools.** Wireshark, the OpenPLC Editor and the Kali desktop stay in
  the virtual stack.
- **No Metasploit.** `training/opcua/opcua_login.py` does with asyncua what
  the msf-opcua modules do.
- **No internet on a board.** Everything the challenges need is in the image.

## Building

The build context is the repository root, like the landing image's, because
the image carries its own copy of `training/`:

```sh
docker build -f software/attack-shell/Dockerfile -t cybics-attack-shell .
```

The arm64 image for the board is about 100 MB compressed (about 315 MB
unpacked) and shares the `python:3.12-alpine` base layers with the landing
image.
