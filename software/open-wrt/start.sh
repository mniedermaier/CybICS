#!/bin/sh

ip tuntap add dev tap0 mode tap
ip tuntap add dev tap1 mode tap

ip link set tap0 master br-ext
ip link set tap1 master br-int

ip link set tap0 up
ip link set tap1 up

exec qemu-system-x86_64 \
    -nographic \
    -m 256M \
    -drive file=openwrt.img,format=raw \
    -serial mon:stdio \
    -netdev tap,id=n0,ifname=tap0,script=no,downscript=no \
    -device e1000,netdev=n0 \
    -netdev tap,id=n1,ifname=tap1,script=no,downscript=no \
    -device e1000,netdev=n1