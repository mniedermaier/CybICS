# Multi-stage build for Zephyr firmware with OpenOCD flashing
# Stage 1: Build the firmware
FROM ghcr.io/zephyrproject-rtos/zephyr-build:v0.26.6 AS build

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Zephyr SDK
ARG ZEPHYR_SDK_VERSION=0.16.5
RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz && \
    mkdir -p /opt/zephyr-sdk && \
    tar -xf zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz -C /opt/zephyr-sdk --strip-components=1 && \
    rm zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz && \
    /opt/zephyr-sdk/setup.sh -t arm-zephyr-eabi -h -c

ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr

# Initialize Zephyr workspace
WORKDIR /workspace
RUN west init -m https://github.com/zephyrproject-rtos/zephyr --mr v3.5.0 && \
    west update && \
    west zephyr-export && \
    pip3 install -r /workspace/zephyr/scripts/requirements.txt

# Copy project files
COPY . /workspace/app

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

# Copy OpenOCD configuration
COPY openocd_rpi.cfg ./

# Expose OpenOCD ports
# 3333: GDB server
# 4444: Telnet server
EXPOSE 3333
EXPOSE 4444

# Flash the firmware and keep OpenOCD running as a GDB server
CMD openocd -f /CybICS/openocd_rpi.cfg -c "program CybICS.bin verify reset exit 0x08000000" && \
    sleep 5 && \
    openocd -f /CybICS/openocd_rpi.cfg
