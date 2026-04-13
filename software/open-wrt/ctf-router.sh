#!/bin/bash
# Startet/stoppt die CTF Router Challenge.
# Der OpenWrt-Router wird zwischen Angreifer und ICS-Netz gehängt.
# Usage: ./ctf-router.sh start|stop|status

set -uo pipefail

# --- Config ---
ROUTER_DIR="$(cd "$(dirname "$0")" && pwd)"
ROUTER_CONTAINER="open-wrt-openwrt-1"
INT_NET="virtual_virt-cybics"
EXT_NET="ext_ctf"
EXT_SUBNET="172.22.0.0/24"
EXT_GATEWAY="172.22.0.1"
ROUTER_INT_IP="172.18.0.50"
ROUTER_EXT_IP="172.22.0.2"
ATTACK_EXT_IP="172.22.0.100"
ATTACK_CONTAINER="attack-machine"

find_container() {
    docker ps --format '{{.Names}}' | grep -i "$1" | head -1
}

container_in_network() {
    docker inspect "$1" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null | grep -q "$2"
}

# --- START ---
do_start() {
    echo "Starting CTF router challenge..."

    # CybICS muss laufen
    if ! docker network ls --format '{{.Name}}' | grep -q "$INT_NET"; then
        echo "ERROR: $INT_NET not found. Start CybICS first."
        exit 1
    fi

    ATTACK=$(find_container "$ATTACK_CONTAINER")
    [ -n "$ATTACK" ] && echo "Found attack machine: $ATTACK"

    # ext_ctf Netz anlegen
    if ! docker network ls --format '{{.Name}}' | grep -q "^${EXT_NET}$"; then
        docker network create --driver bridge --subnet "$EXT_SUBNET" --gateway "$EXT_GATEWAY" "$EXT_NET" \
            || { echo "ERROR: could not create $EXT_NET"; exit 1; }
    fi

    # Router hochfahren
    (cd "$ROUTER_DIR" && docker compose up -d --build)
    sleep 3
    if ! docker ps --format '{{.Names}}' | grep -q "$ROUTER_CONTAINER"; then
        echo "ERROR: router container not running"
        exit 1
    fi

    # Router in beide Netze hängen
    container_in_network "$ROUTER_CONTAINER" "$INT_NET" \
        || docker network connect --ip "$ROUTER_INT_IP" "$INT_NET" "$ROUTER_CONTAINER"
    container_in_network "$ROUTER_CONTAINER" "$EXT_NET" \
        || docker network connect --ip "$ROUTER_EXT_IP" "$EXT_NET" "$ROUTER_CONTAINER"

    # Attack-Machine zusätzlich ins ext_ctf (bleibt im internen wegen Docker port-mapping Limitation)
    if [ -n "$ATTACK" ]; then
        container_in_network "$ATTACK" "$EXT_NET" \
            || docker network connect --ip "$ATTACK_EXT_IP" "$EXT_NET" "$ATTACK"
    fi

    # Warten bis SSH antwortet
    echo -n "Waiting for router SSH"
    for _ in $(seq 1 24); do
        nc -z -w2 127.0.0.1 2222 2>/dev/null && break
        echo -n "."
        sleep 5
    done
    echo " ok"

    echo ""
    echo "CTF router challenge running."
    echo ""
    echo "Router:"
    echo "  internal  $ROUTER_INT_IP (virt-cybics)"
    echo "  external  $ROUTER_EXT_IP (ext_ctf)"
    echo "  SSH       localhost:2222 (root/password)"
    echo ""
    echo "From a Kali VM (real isolation):"
    echo "  nmap <host-ip>  ->  find port 2222"
    echo "  ssh root@<host-ip> -p 2222"
    echo "  then pivot into 172.18.0.0/24"
    echo ""
    if [ -n "$ATTACK" ]; then
        echo "Attack machine: $ATTACK_EXT_IP in ext_ctf"
        echo "  (stays in virt-cybics too — docker limitation)"
        echo "  noVNC still at localhost:6081"
    fi
}

# --- STOP ---
do_stop() {
    echo "Stopping CTF router challenge..."

    ATTACK=$(find_container "$ATTACK_CONTAINER")
    if [ -n "$ATTACK" ]; then
        container_in_network "$ATTACK" "$EXT_NET" \
            && docker network disconnect "$EXT_NET" "$ATTACK" 2>/dev/null
    fi

    if docker ps --format '{{.Names}}' | grep -q "$ROUTER_CONTAINER"; then
        (cd "$ROUTER_DIR" && docker compose down --timeout 5)
    fi

    docker network ls --format '{{.Name}}' | grep -q "^${EXT_NET}$" \
        && docker network rm "$EXT_NET" 2>/dev/null

    echo "Stopped. Back to normal."
}

# --- STATUS ---
do_status() {
    echo "CTF Router Challenge status:"
    echo ""

    if docker ps --format '{{.Names}}' | grep -q "$ROUTER_CONTAINER"; then
        echo "  router:    running"
        container_in_network "$ROUTER_CONTAINER" "$INT_NET" && echo "    -> $INT_NET ($ROUTER_INT_IP)"
        container_in_network "$ROUTER_CONTAINER" "$EXT_NET" && echo "    -> $EXT_NET ($ROUTER_EXT_IP)"
    else
        echo "  router:    not running"
    fi

    if docker network ls --format '{{.Name}}' | grep -q "^${EXT_NET}$"; then
        echo "  ext_ctf:   exists"
    else
        echo "  ext_ctf:   not created"
    fi

    ATTACK=$(find_container "$ATTACK_CONTAINER")
    if [ -n "$ATTACK" ]; then
        if container_in_network "$ATTACK" "$EXT_NET"; then
            echo "  attack-vm: ctf mode (ext_ctf + virt-cybics)"
        else
            echo "  attack-vm: normal (virt-cybics only)"
        fi
    else
        echo "  attack-vm: not found"
    fi
    echo ""
}

case "${1:-}" in
    start)  do_start ;;
    stop)   do_stop ;;
    status) do_status ;;
    *)      echo "Usage: $0 {start|stop|status}"; exit 1 ;;
esac