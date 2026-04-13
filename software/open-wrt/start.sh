#!/bin/sh

ip tuntap add dev tap0 mode tap
ip tuntap add dev tap1 mode tap

# Container-namespace Bridges erstellen (OS-unabhängig, kein Host-Bridge-Zugriff nötig)
ip link add br-ext type bridge
ip link add br-int type bridge

# IPs der Docker-Interfaces entfernen (Bridge übernimmt L2-Forwarding)
ip addr flush dev eth0
ip addr flush dev eth1

# Docker-Interfaces an Bridges binden
ip link set eth0 master br-ext
ip link set eth1 master br-int

# QEMU-TAP-Devices an Bridges binden
ip link set tap0 master br-ext
ip link set tap1 master br-int

# Alle Interfaces hochbringen
ip link set br-ext up
ip link set br-int up
ip link set eth0 up
ip link set eth1 up
ip link set tap0 up
ip link set tap1 up

echo "TAP bridging enabled (container namespace)"

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