FROM debian:12-slim

# Install OpenOCD and tools for flash verification
RUN apt-get update && apt-get install -y \
    openocd \
    binutils \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS

# Copy the built firmware binary
COPY build/zephyr/zephyr.bin ./CybICS.bin
COPY build/zephyr/zephyr.elf ./CybICS.elf

# Copy OpenOCD configuration and flash script
COPY openocd_rpi.cfg ./
COPY openocd_virtual_server.py ./
COPY flash_if_needed.sh ./
RUN chmod +x /CybICS/flash_if_needed.sh /CybICS/openocd_virtual_server.py

# Expose OpenOCD ports
EXPOSE 3333 4444

# Check firmware version and flash only if needed, then start GDB server
CMD ["/CybICS/flash_if_needed.sh"]
