# Multi-stage build with cached Zephyr workspace
# Stage 1: Build the firmware
FROM ghcr.io/zephyrproject-rtos/zephyr-build:v0.26.6 AS build

# Initialize Zephyr workspace (this layer will be cached)
WORKDIR /workspace
RUN west init -m https://github.com/zephyrproject-rtos/zephyr --mr v3.5.0 && \
    west update && \
    west zephyr-export && \
    pip3 install -r /workspace/zephyr/scripts/requirements.txt

# Set Zephyr environment
ENV ZEPHYR_BASE=/workspace/zephyr

# Copy project files (separate layer so changes don't rebuild workspace)
# Use --chown to ensure correct permissions
COPY --chown=user:user . /workspace/app

# Build the firmware
WORKDIR /workspace/app
USER user
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

# Copy OpenOCD configuration
COPY openocd_rpi.cfg ./

# Expose OpenOCD ports
EXPOSE 3333 4444

# Flash the firmware and keep OpenOCD running as a GDB server
CMD openocd -f /CybICS/openocd_rpi.cfg -c "program CybICS.bin verify reset exit 0x08000000" && \
    sleep 5 && \
    openocd -f /CybICS/openocd_rpi.cfg
