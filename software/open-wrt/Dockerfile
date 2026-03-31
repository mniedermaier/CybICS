FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    qemu-system-x86 \
    wget \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /openwrt

RUN wget -q https://downloads.openwrt.org/releases/24.10.5/targets/x86/64/openwrt-24.10.5-x86-64-generic-ext4-combined.img.gz \
    && gunzip openwrt-24.10.5-x86-64-generic-ext4-combined.img.gz; \
    EC=$?; [ $EC -eq 0 ] || [ $EC -eq 2 ] \
    && mv openwrt-24.10.5-x86-64-generic-ext4-combined.img openwrt.img

COPY 99-wan-config /tmp/99-wan-config

RUN dd if=openwrt.img of=partition2.img bs=512 skip=33792 2>/dev/null \
    && printf 'cd /etc/uci-defaults\nwrite /tmp/99-wan-config 99-wan-config\n' | debugfs -w partition2.img \
    && dd if=partition2.img of=openwrt.img bs=512 seek=33792 conv=notrunc 2>/dev/null \
    && rm partition2.img

COPY start.sh start.sh
RUN chmod +x start.sh

CMD ["/openwrt/start.sh"]