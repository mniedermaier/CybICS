#!/bin/bash
# test-router.sh — Build & test CybICS OpenWrt router
# Baut mit --no-cache, startet den Stack, prüft SSH-Erreichbarkeit

COMPOSE_FILE="docker-compose.yml"
SSH_PORT=2222
SSH_HOST="127.0.0.1"
MAX_WAIT=120
POLL_INTERVAL=5

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

passed=0
failed=0

log()  { echo -e "${YELLOW}[TEST]${NC} $*"; }
pass() { echo -e "${GREEN}[PASS]${NC} $*"; ((passed++)); }
fail() { echo -e "${RED}[FAIL]${NC} $*"; ((failed++)); }

cleanup() {
    log "Räume auf..."
    docker compose -f "$COMPOSE_FILE" down --timeout 5 2>/dev/null || true
}
trap cleanup EXIT

# ─── 1. Build ───────────────────────────────────────────────
log "Starte Build (--no-cache)..."
docker compose -f "$COMPOSE_FILE" build --no-cache
BUILD_RC=$?
if [ $BUILD_RC -eq 0 ]; then
    pass "Docker Build erfolgreich"
else
    fail "Docker Build fehlgeschlagen (Exit Code: $BUILD_RC)"
    exit 1
fi

# ─── 2. Stack starten ──────────────────────────────────────
log "Starte Stack..."
UP_OUTPUT=$(docker compose -f "$COMPOSE_FILE" up -d 2>&1)
UP_RC=$?
if [ $UP_RC -ne 0 ]; then
    fail "Stack konnte nicht gestartet werden (Exit Code: $UP_RC)"
    echo "$UP_OUTPUT"
    echo ""
    log "Tipp: Versuch 'docker network prune -f' und dann nochmal."
    exit 1
fi

sleep 3

# Container-Status prüfen
CONTAINER_STATUS=$(docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}" 2>&1)
echo "$CONTAINER_STATUS"

if docker compose -f "$COMPOSE_FILE" ps --status running --format "{{.Name}}" 2>/dev/null | grep -q "openwrt"; then
    pass "OpenWrt-Container läuft"
else
    fail "OpenWrt-Container läuft nicht"
    log "Container-Logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail 30
    exit 1
fi

# ─── 3. Warten bis SSH erreichbar ───────────────────────────
log "Warte auf SSH-Port $SSH_PORT (max ${MAX_WAIT}s)..."
elapsed=0
ssh_ok=false

while [ $elapsed -lt $MAX_WAIT ]; do
    if nc -z -w2 "$SSH_HOST" "$SSH_PORT" 2>/dev/null; then
        ssh_ok=true
        break
    fi
    sleep $POLL_INTERVAL
    elapsed=$((elapsed + POLL_INTERVAL))
    printf "."
done
echo ""

if $ssh_ok; then
    pass "SSH-Port $SSH_PORT erreichbar nach ${elapsed}s"
else
    fail "SSH-Port $SSH_PORT nicht erreichbar nach ${MAX_WAIT}s"
    log "Container-Logs (letzte 50 Zeilen):"
    docker compose -f "$COMPOSE_FILE" logs --tail 50
    exit 1
fi

# Warten bis SSH-Banner kommt (Daemon wirklich bereit)
log "Warte auf SSH-Banner (max 60s)..."
banner_wait=0
banner_ok=false
while [ $banner_wait -lt 60 ]; do
    BANNER=$(echo "" | nc -w3 "$SSH_HOST" "$SSH_PORT" 2>/dev/null || true)
    if echo "$BANNER" | grep -qi "SSH"; then
        banner_ok=true
        break
    fi
    sleep 5
    banner_wait=$((banner_wait + 5))
    printf "."
done
echo ""

if $banner_ok; then
    pass "SSH-Daemon bereit nach $((elapsed + banner_wait))s"
    log "Warte 20s auf uci-defaults (Passwort setzen)..."
    sleep 20
else
    fail "SSH-Banner nicht erhalten nach 60s"
    log "Container-Logs (letzte 30 Zeilen):"
    docker compose -f "$COMPOSE_FILE" logs --tail 30
fi

# ─── 4. SSH-Login testen ────────────────────────────────────
log "Teste SSH-Login..."
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"

if ! command -v sshpass &>/dev/null; then
    log "⚠ sshpass nicht installiert — überspringe Login-Tests"
    log "  Installieren mit: brew install hudochenkov/sshpass/sshpass"
else
    SSH_CMD="sshpass -p password ssh $SSH_OPTS -p $SSH_PORT root@$SSH_HOST"

    LOGIN_OUTPUT=$($SSH_CMD "echo ok" 2>&1)
    LOGIN_RC=$?
    if [ $LOGIN_RC -eq 0 ] && echo "$LOGIN_OUTPUT" | grep -q "ok"; then
        pass "SSH-Login mit root/password erfolgreich"

        # ─── 5. Netzwerk-Checks innerhalb OpenWrt ───────────
        log "Prüfe Netzwerk-Interfaces in OpenWrt..."

        iface_count=$($SSH_CMD "ip -o link show | grep -c 'eth'" 2>/dev/null || echo "0")
        if [ "$iface_count" -ge 3 ]; then
            pass "Alle 3 NICs vorhanden ($iface_count eth-Interfaces)"
        else
            fail "Nur $iface_count eth-Interface(s) gefunden, erwartet: 3"
            $SSH_CMD "ip -o link show" 2>/dev/null || true
        fi

        wan_check=$($SSH_CMD "ip -4 addr show | grep '172\.20\.0\.2'" 2>/dev/null || echo "")
        if echo "$wan_check" | grep -q "172.20.0.2"; then
            pass "WAN-IP korrekt: 172.20.0.2"
        else
            fail "WAN-IP 172.20.0.2 auf keinem Interface gefunden"
            log "Alle IPs:"
            $SSH_CMD "ip -4 addr show" 2>/dev/null || true
        fi

        fw_check=$($SSH_CMD "uci show firewall.@zone[0].network" 2>/dev/null || echo "")
        if echo "$fw_check" | grep -q "qemu"; then
            pass "eth2 (qemu) ist in der LAN-Firewall-Zone"
        else
            fail "eth2 (qemu) fehlt in der Firewall-Zone"
            log "Firewall-Config: $fw_check"
        fi
    else
        fail "SSH-Login fehlgeschlagen (Exit Code: $LOGIN_RC)"
        echo "$LOGIN_OUTPUT"
    fi
fi

# ─── 6. Ping vom test-Container zum Router ──────────────────
log "Teste Ping test→Router..."
PING_OUTPUT=$(docker compose -f "$COMPOSE_FILE" exec -T test ping -c 2 -W 3 172.20.0.2 2>&1)
PING_RC=$?
if [ $PING_RC -eq 0 ]; then
    pass "test-Container kann Router (172.20.0.2) pingen"
else
    fail "test-Container kann Router nicht erreichen"
    echo "$PING_OUTPUT"
fi

# ─── Ergebnis ────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════"
echo -e "  Ergebnis: ${GREEN}${passed} bestanden${NC}, ${RED}${failed} fehlgeschlagen${NC}"
echo "═══════════════════════════════════════"

[ $failed -eq 0 ] && exit 0 || exit 1