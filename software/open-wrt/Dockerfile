FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    qemu-system-x86 \
    wget && rm -rf /var/lib/apt/lists/*

WORKDIR /openwrt

RUN wget -q https://downloads.openwrt.org/releases/24.10.5/targets/x86/64/openwrt-24.10.5-x86-64-generic-ext4-combined.img.gz \
    && gunzip openwrt-24.10.5-x86-64-generic-ext4-combined.img.gz; \
    EC=$?; [ $EC -eq 0 ] || [ $EC -eq 2 ] \
    && mv openwrt-24.10.5-x86-64-generic-ext4-combined.img openwrt.img

CMD ["qemu-system-x86_64", \
     "-nographic", \
     "-m", "256M", \
     "-drive", "file=openwrt.img,format=raw", \
     "-serial", "mon:stdio"]