# Multi-stage build with cached Zephyr workspace
# Stage 1: Build the firmware
FROM ghcr.io/zephyrproject-rtos/zephyr-build:v0.28.7 AS build

WORKDIR /workspace

# Copy project files first (includes west.yml manifest)
COPY --chown=user:user . /workspace/app

# Initialize Zephyr workspace using project manifest (downloads only required modules)
USER user
RUN west init -l app && \
    west update --narrow -o=--depth=1 && \
    pip3 install -r zephyr/scripts/requirements.txt

# Set Zephyr environment
ENV ZEPHYR_BASE=/workspace/zephyr

# Build the firmware
WORKDIR /workspace/app
RUN west build -b nucleo_g070rb

# Stage 2: Runtime container with OpenOCD
FROM debian:12-slim

# Install OpenOCD
RUN apt-get update && apt-get install -y \
    openocd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS

# Copy the built firmware binary
COPY --from=build /workspace/app/build/zephyr/zephyr.bin ./CybICS.bin
COPY --from=build /workspace/app/build/zephyr/zephyr.elf ./CybICS.elf

# Copy OpenOCD configuration and flash script
COPY openocd_rpi.cfg ./
COPY flash_if_needed.sh ./
RUN chmod +x /CybICS/flash_if_needed.sh

# Expose OpenOCD ports
EXPOSE 3333 4444

# Check firmware version and flash only if needed, then start GDB server
CMD ["/CybICS/flash_if_needed.sh"]
