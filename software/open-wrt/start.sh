#!/bin/sh

ip tuntap add dev tap0 mode tap
ip tuntap add dev tap1 mode tap

# Bridges nur auf Linux verfügbar
if ip link show br-ext > /dev/null 2>&1; then
    ip link set tap0 master br-ext
    ip link set tap1 master br-int
    echo "TAP bridging enabled"
else
    echo "Warning: br-ext/br-int not available (macOS Docker Desktop), TAP bridging disabled"
fi

ip link set tap0 up
ip link set tap1 up

ARCH=$(uname -m)

if [ "$ARCH" = "aarch64" ]; then
    exec qemu-system-aarch64 \
        -nographic \
        -machine virt \
        -cpu cortex-a57 \
        -m 256M \
        -drive file=openwrt.img,format=raw \
        -bios /usr/share/qemu-efi-aarch64/QEMU_EFI.fd \
        -serial mon:stdio \
        -netdev tap,id=n0,ifname=tap0,script=no,downscript=no \
        -device virtio-net-pci,netdev=n0 \
        -netdev tap,id=n1,ifname=tap1,script=no,downscript=no \
        -device virtio-net-pci,netdev=n1 \
        -netdev user,id=n2,hostfwd=tcp::2222-:22 \
        -device virtio-net-pci,netdev=n2
else
    exec qemu-system-x86_64 \
        -nographic \
        -m 128M \
        -drive file=openwrt.img,format=raw \
        -serial mon:stdio \
        -netdev tap,id=n0,ifname=tap0,script=no,downscript=no \
        -device e1000,netdev=n0 \
        -netdev tap,id=n1,ifname=tap1,script=no,downscript=no \
        -device e1000,netdev=n1 \
        -netdev user,id=n2,hostfwd=tcp::2222-:22 \
        -device e1000,netdev=n2
fi