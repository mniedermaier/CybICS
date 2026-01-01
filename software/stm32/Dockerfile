FROM debian:12-slim

# Install OpenOCD and xxd (for version extraction from binary)
RUN apt-get update && apt-get install -y \
    openocd \
    xxd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS

# Copy the built firmware binary
COPY build/zephyr/zephyr.bin ./CybICS.bin
COPY build/zephyr/zephyr.elf ./CybICS.elf

# Copy OpenOCD configuration and flash script
COPY openocd_rpi.cfg ./
COPY flash_if_needed.sh ./
RUN chmod +x /CybICS/flash_if_needed.sh

# Expose OpenOCD ports
EXPOSE 3333 4444

# Check firmware version and flash only if needed, then start GDB server
CMD ["/CybICS/flash_if_needed.sh"]
