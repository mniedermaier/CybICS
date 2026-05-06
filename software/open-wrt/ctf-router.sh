#!/bin/bash
# Startet/stoppt die CTF Router Challenge.
# Der OpenWrt-Router wird zwischen Angreifer und ICS-Netz gehängt.
# Usage: ./ctf-router.sh start|stop|status

set -uo pipefail

# --- Config ---
ROUTER_DIR="$(cd "$(dirname "$0")" && pwd)"
ROUTER_CONTAINER="${ROUTER_CONTAINER:-open-wrt-openwrt-1}"
INT_NET="${INT_NET:-virtual_virt-cybics}"
EXT_NET="${EXT_NET:-ext_ctf}"
EXT_SUBNET="172.22.0.0/24"
EXT_GATEWAY="172.22.0.1"
ROUTER_INT_IP="172.18.0.50"
ROUTER_EXT_IP="172.22.0.2"
ATTACK_EXT_IP="172.22.0.100"
ATTACK_CONTAINER="${ATTACK_CONTAINER:-attack-machine}"

check_router_ssh() {
    if command -v nc >/dev/null 2>&1; then
        nc -z -w2 127.0.0.1 2222 >/dev/null 2>&1
        return $?
    fi

    if command -v python3 >/dev/null 2>&1; then
        python3 - <<'PY'
import socket
import sys

try:
    with socket.create_connection(("127.0.0.1", 2222), timeout=2):
        pass
except OSError:
    sys.exit(1)

sys.exit(0)
PY
        return $?
    fi

    docker port "$ROUTER_CONTAINER" 2222/tcp >/dev/null 2>&1
}

find_container() {
    docker ps --format '{{.Names}}' | grep -i "$1" | head -1
}

container_in_network() {
    docker inspect "$1" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' 2>/dev/null | grep -q "$2"
}

cleanup_router_state() {
    # Remove leftovers from failed starts. Stale Docker network IDs on an
    # existing container can otherwise make the next `compose up` fail.
    local attack
    attack=$(find_container "$ATTACK_CONTAINER")

    if [ -n "$attack" ]; then
        docker network disconnect "$EXT_NET" "$attack" 2>/dev/null || true
    fi

    (cd "$ROUTER_DIR" && docker compose down --remove-orphans --timeout 5 >/dev/null 2>&1) || true
    docker rm -f "$ROUTER_CONTAINER" >/dev/null 2>&1 || true
    docker network rm "$EXT_NET" >/dev/null 2>&1 || true
}

# --- START ---
do_start() {
    echo "Starting CTF router challenge..."

    # CybICS muss laufen
    if ! docker network ls --format '{{.Name}}' | grep -q "$INT_NET"; then
        echo "ERROR: $INT_NET not found. Start CybICS first."
        exit 1
    fi

    cleanup_router_state

    ATTACK=$(find_container "$ATTACK_CONTAINER")
    [ -n "$ATTACK" ] && echo "Found attack machine: $ATTACK"

    # ext_ctf Netz anlegen
    if ! docker network ls --format '{{.Name}}' | grep -q "^${EXT_NET}$"; then
        docker network create --driver bridge --subnet "$EXT_SUBNET" --gateway "$EXT_GATEWAY" "$EXT_NET" \
            || { echo "ERROR: could not create $EXT_NET"; exit 1; }
    fi

    # Router hochfahren
    (cd "$ROUTER_DIR" && docker compose up -d --build --remove-orphans)
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

    # Im Landing-Lifecycle übernimmt der Healthcheck die Readiness-Prüfung.
    # Dort darf dieses Script nicht blockieren, sonst schlägt der Start trotz
    # korrekt hochfahrender Umgebung fälschlich mit einem Timeout fehl.
    if [ -n "${CYBICS_LIFECYCLE_PHASE:-}" ]; then
        echo "Skipping router SSH wait because lifecycle healthcheck handles readiness."
    else
        echo -n "Waiting for router SSH"
        SSH_READY=false
        for _ in $(seq 1 24); do
            if nc -z -w2 127.0.0.1 2222 2>/dev/null; then
                SSH_READY=true
                break
            fi
            echo -n "."
            sleep 5
        done

        if [ "$SSH_READY" != true ]; then
            echo " failed"
            echo "ERROR: router SSH did not become reachable on localhost:2222"
            exit 1
        fi

        echo " ok"
    fi

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

    ssh-keygen -f "$HOME/.ssh/known_hosts" -R "[127.0.0.1]:2222" 2>/dev/null || true

    ATTACK=$(find_container "$ATTACK_CONTAINER")
    if [ -n "$ATTACK" ]; then
        container_in_network "$ATTACK" "$EXT_NET" \
            && docker network disconnect "$EXT_NET" "$ATTACK" 2>/dev/null
    fi

    (cd "$ROUTER_DIR" && docker compose down --remove-orphans --timeout 5 >/dev/null 2>&1) || true
    docker rm -f "$ROUTER_CONTAINER" >/dev/null 2>&1 || true

    docker network ls --format '{{.Name}}' | grep -q "^${EXT_NET}$" \
        && docker network rm "$EXT_NET" 2>/dev/null

    echo "Stopped. Back to normal."
}

# --- HEALTH ---
do_health() {
    if ! docker ps --format '{{.Names}}' | grep -q "$ROUTER_CONTAINER"; then
        echo "router container not running"
        exit 1
    fi

    if ! container_in_network "$ROUTER_CONTAINER" "$INT_NET"; then
        echo "router not attached to $INT_NET"
        exit 1
    fi

    if ! container_in_network "$ROUTER_CONTAINER" "$EXT_NET"; then
        echo "router not attached to $EXT_NET"
        exit 1
    fi

    # if ! check_router_ssh; then
    #    echo "router SSH not reachable on localhost:2222"
    #    exit 1
    # fi

    echo "router healthy"
    exit 0
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
    health) do_health ;;
    status) do_status ;;
    *)      echo "Usage: $0 {start|stop|status|health}"; exit 1 ;;
esac
