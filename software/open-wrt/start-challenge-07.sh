#!/bin/bash
set -e
$ROUTER_NET="challenge07_ext_net"


echo "[*] Starting Challenge 07: Router Pivoting..."

# Router starten
echo "[*] Starting router container..."
docker compose -p challenge07 -f docker-compose.yml up -d

# Attack-Machine Container finden
ATTACK_CONTAINER=$(docker ps --format '{{.Names}}' | grep 'attack-machine' | head -1)

if [ -z "$ATTACK_CONTAINER" ]; then
    echo "[!] Error: attack-machine container not found. Is the base environment running?"
    exit 1
fi

echo "[*] Found attack-machine: $ATTACK_CONTAINER"

# Attack-Machine vom internen Netz trennen
echo "[*] Disconnecting attack-machine from virt-cybics..."
docker network disconnect virtual_virt-cybics "$ATTACK_CONTAINER"

# Attack-Machine mit externem Netz verbinden
echo "[*] Connecting attack-machine to ext_net (172.19.0.100)..."
docker network connect --ip 172.19.0.100 $ROUTER_NET "$ATTACK_CONTAINER"

echo ""
echo "[+] Challenge 07 active."
echo "[+]   Attack machine : $ATTACK_CONTAINER @ 172.19.0.100 (ext_net)"
echo "[+]   Router WAN     : 172.19.0.2 (ext_net)"
echo "[+]   Router LAN     : 172.18.0.254 (virt-cybics)"
echo "[+] Pivot through the router to reach the ICS network."
