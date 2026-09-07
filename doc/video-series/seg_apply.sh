#!/usr/bin/env bash
# Host-side helper for the "Network Segmentation" defense lesson (cybics-20).
#
# The attack VM has no Docker access, so the defender applies these iptables
# rules on the ICS host. Each target container drops all traffic from the
# attack machine (172.18.0.100), isolating it from the OT devices. Requires
# NET_ADMIN on the target containers (openplc is privileged; opcua is granted
# cap_add: NET_ADMIN in the compose file and ships iptables in its image).
#
# Usage: seg_apply.sh apply | remove
set -euo pipefail
ATTACK=172.18.0.100
TARGETS=(virtual-openplc-1 virtual-opcua-1)
case "${1:-}" in
  apply)
    for c in "${TARGETS[@]}"; do
      docker exec "$c" iptables -A INPUT -s "$ATTACK" -j DROP
      echo "$c: DROP $ATTACK added"
    done ;;
  remove)
    for c in "${TARGETS[@]}"; do
      docker exec "$c" iptables -D INPUT -s "$ATTACK" -j DROP 2>/dev/null || true
      echo "$c: DROP $ATTACK removed"
    done ;;
  *) echo "usage: $0 apply|remove"; exit 1 ;;
esac
