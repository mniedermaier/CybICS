#!/bin/bash
set -e
$ROUTER_NET="challenge07_ext_net"


echo "[*] Stopping Challenge 07: Router Pivoting..."

# Attack-Machine Container finden
ATTACK_CONTAINER=$(docker ps --format '{{.Names}}' | grep 'attack-machine' | head -1)

if [ -z "$ATTACK_CONTAINER" ]; then
    echo "[!] Warning: attack-machine container not found, skipping network rollback."
else
    echo "[*] Found attack-machine: $ATTACK_CONTAINER"

    # Attack-Machine wieder mit internem Netz verbinden
    echo "[*] Reconnecting attack-machine to virt-cybics (172.18.0.100)..."
    docker network connect --ip 172.18.0.100 virtual_virt-cybics "$ATTACK_CONTAINER"

    # Attack-Machine vom externen Netz trennen
    echo "[*] Disconnecting attack-machine from ext_net..."
    docker network disconnect $ROUTER_NET "$ATTACK_CONTAINER"
fi

# Router stoppen
echo "[*] Stopping router container..."
docker compose -p challenge07 -f docker-compose.yml down

echo ""
echo "[+] Challenge 07 stopped."
echo "[+]   Attack machine restored to virt-cybics @ 172.18.0.100"
