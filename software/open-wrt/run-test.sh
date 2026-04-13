#!/bin/bash
# Stoppe alte Tests
docker compose -f docker-compose.test.yml down

echo "[*] Baue Router-Image..."
docker compose -f docker-compose.test.yml build --no-cache

echo "[*] Starte Test-Umgebung..."
docker compose -f docker-compose.test.yml up -d

echo "[*] Warte 60 Sekunden auf OpenWrt Boot..."
sleep 60

echo "[*] TEST 1: Ping von WAN-Probe zum Router (WAN-Interface)..."
docker exec open-wrt-wan-probe-1 ping -c 3 172.19.0.2

echo "[*] TEST 2: Ping von WAN-Probe durch den Router zur LAN-Probe..."
docker exec open-wrt-wan-probe-1 ping -c 3 172.18.0.10

if [ $? -eq 0 ]; then
    echo -e "\n[+] ERFOLG: Der Router leitet Traffic korrekt weiter!"
else
    echo -e "\n[-] FEHLER: Routing funktioniert nicht. Prüfe 'docker logs router-test'."
fi