#!/usr/bin/env bash
# =============================================================================
# training/flash_dump/build.sh
#
# Run from within training/flash_dump/:
#   sudo ./build.sh
#
# Outputs:
#   flash_dump.bin.gz     <- commit this into the repo
#   dist/flash_dump.bin   <- local uncompressed copy (gitignored)
#   dist/unlock_firmware  <- local compiled binary (gitignored)
#
# Flash layout:
#   0x000000  boot header + partition table
#   0x000080  32-byte LUKS key
#   0x010000  ext2 filesystem (contains unlock_firmware)
#   0x200000  LUKS2 container (contains flag.txt)
#
# Requirements: gcc, cryptsetup, python3, mke2fs (e2fsprogs), gzip
# Must be run as root (cryptsetup + mount needs it)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"

# --- constants ----------------------------------------------------------------
KEY_OFFSET=128          # 0x80
KEY_LEN=32
EXT2_OFFSET=65536       # 0x10000
EXT2_SIZE_MB=1
LUKS_OFFSET=2097152     # 0x200000
LUKS_SIZE_MB=32
FLASH_SIZE_MB=64
FLAG="CybICS(fl4sh_dump_4nalyz3d)"

OUT_DUMP="$DIST_DIR/flash_dump.bin"
OUT_BINARY="$DIST_DIR/unlock_firmware"
OUT_LUKS="$DIST_DIR/luks.img"
OUT_EXT2="$DIST_DIR/rootfs.img"
OUT_GZ="$SCRIPT_DIR/flash_dump.bin.gz"

MAPPER="flash_challenge_luks"
MNT_LUKS="/tmp/flash_challenge_luks"
MNT_EXT2="/tmp/flash_challenge_ext2"

# --- helpers ------------------------------------------------------------------
info() { echo "[*] $*"; }
ok()   { echo "[+] $*"; }
err()  { echo "[-] $*" >&2; exit 1; }

# --- checks -------------------------------------------------------------------
[[ $EUID -eq 0 ]] || err "Run as root (needed for cryptsetup + mount)"
command -v gcc        &>/dev/null || err "gcc not found"
command -v cryptsetup &>/dev/null || err "cryptsetup not found"
command -v python3    &>/dev/null || err "python3 not found"
command -v mke2fs     &>/dev/null || err "mke2fs not found (install e2fsprogs)"
command -v gzip       &>/dev/null || err "gzip not found"

# --- setup dist dir -----------------------------------------------------------
mkdir -p "$DIST_DIR"

# --- compile binary -----------------------------------------------------------
info "Compiling unlock_firmware..."
gcc -O0 -g -o "$OUT_BINARY" "$SCRIPT_DIR/unlock_firmware.c"
ok "dist/unlock_firmware compiled"

# --- generate key -------------------------------------------------------------
info "Generating 32-byte LUKS key..."
python3 -c "
import secrets, sys
key = secrets.token_bytes(32)
open('$DIST_DIR/key.bin','wb').write(key)
sys.stderr.write('[+] Key: ' + key.hex() + '\n')
"

# --- create ext2 with unlock_firmware -----------------------------------------
info "Creating ext2 rootfs (${EXT2_SIZE_MB}MB)..."
dd if=/dev/zero of="$OUT_EXT2" bs=1M count=$EXT2_SIZE_MB status=none
mke2fs -t ext2 -L "rootfs" "$OUT_EXT2" 2>/dev/null
mkdir -p "$MNT_EXT2"
mount -o loop "$OUT_EXT2" "$MNT_EXT2"
mkdir -p "$MNT_EXT2/usr/sbin"
cp "$OUT_BINARY" "$MNT_EXT2/usr/sbin/unlock_firmware"
umount "$MNT_EXT2"
rmdir "$MNT_EXT2"
ok "ext2 rootfs ready"

# --- create LUKS container ----------------------------------------------------
info "Creating LUKS2 container (${LUKS_SIZE_MB}MB)..."
dd if=/dev/zero of="$OUT_LUKS" bs=1M count=$LUKS_SIZE_MB status=none
cryptsetup luksFormat --type luks2 --batch-mode --key-file "$DIST_DIR/key.bin" "$OUT_LUKS"
cryptsetup open --type luks2 --key-file "$DIST_DIR/key.bin" "$OUT_LUKS" "$MAPPER"
mkfs.ext4 -q -L "firmware" /dev/mapper/$MAPPER
mkdir -p "$MNT_LUKS"
mount /dev/mapper/$MAPPER "$MNT_LUKS"
mkdir -p "$MNT_LUKS/firmware"
echo "$FLAG" > "$MNT_LUKS/firmware/flag.txt"
cat > "$MNT_LUKS/firmware/version.txt" << 'EOF'
CybICS Industrial Controller Firmware
Version: 1.4.2
This firmware is proprietary and confidential.
EOF
umount "$MNT_LUKS"
cryptsetup close "$MAPPER"
rmdir "$MNT_LUKS"
ok "LUKS container ready"

# --- assemble flash dump ------------------------------------------------------
info "Assembling flash_dump.bin (${FLASH_SIZE_MB}MB)..."
dd if=/dev/zero of="$OUT_DUMP" bs=1M count=$FLASH_SIZE_MB status=none

python3 << PYEOF
import struct

data = bytearray(open("$OUT_DUMP", "rb").read())
data[0:10] = b'\xEB\x58\x90CYBFLSH1\x00'
data[0x10:0x20] = struct.pack("<IIII", 0x80,     0x80,      0xCAFE, 0x01)
data[0x20:0x30] = struct.pack("<IIII", 0x10000,  0x100000,  0xDEAD, 0x02)
data[0x30:0x40] = struct.pack("<IIII", 0x200000, 0x2000000, 0xBEEF, 0x03)
key = open("$DIST_DIR/key.bin", "rb").read()
data[$KEY_OFFSET : $KEY_OFFSET + $KEY_LEN] = key
open("$OUT_DUMP", "wb").write(data)
PYEOF

dd if="$OUT_EXT2" of="$OUT_DUMP" bs=512 seek=$(( EXT2_OFFSET / 512 )) conv=notrunc status=none
dd if="$OUT_LUKS" of="$OUT_DUMP" bs=512 seek=$(( LUKS_OFFSET / 512 )) conv=notrunc status=none
ok "Flash dump assembled"

# --- cleanup intermediate files -----------------------------------------------
rm -f "$DIST_DIR/key.bin" "$OUT_LUKS" "$OUT_EXT2"

# --- compress for repo --------------------------------------------------------
info "Compressing -> flash_dump.bin.gz..."
gzip -9 -c "$OUT_DUMP" > "$OUT_GZ"
ok "$(du -h "$OUT_GZ" | cut -f1) -> flash_dump.bin.gz"

# --- done ---------------------------------------------------------------------
echo ""
ok "====================================="
ok " dist/flash_dump.bin   $(du -h "$OUT_DUMP"   | cut -f1)  (local only)"
ok " dist/unlock_firmware  $(du -h "$OUT_BINARY" | cut -f1)  (local only)"
ok " flash_dump.bin.gz     $(du -h "$OUT_GZ"     | cut -f1)  (commit this)"
ok "====================================="