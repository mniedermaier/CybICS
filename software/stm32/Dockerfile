# ─── Stage 1: Build Zephyr firmware ──────────────────────────────────────────
FROM --platform=linux/amd64 ubuntu:22.04 AS builder

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install base dependencies and Zephyr requirements
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-wheel \
    curl \
    wget \
    xz-utils \
    file \
    make \
    cmake \
    ninja-build \
    gperf \
    ccache \
    dfu-util \
    device-tree-compiler \
    gcc \
    gcc-multilib \
    g++-multilib \
    libsdl2-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Allow west extension commands in all directories
RUN git config --system --add safe.directory '*'

# Create non-root user (matches .devcontainer/stm32 setup)
RUN addgroup --gid 1000 docker \
    && adduser --uid 1000 --ingroup docker --home /home/docker --disabled-password --gecos "" docker

WORKDIR /home/docker/zephyrproject

# Ensure non-root user can create the virtualenv and build artifacts in WORKDIR.
RUN chown -R docker:docker /home/docker/zephyrproject

# Copy west manifest FIRST to maximise layer caching:
# The heavy SDK/module download layer is only invalidated when west.yml changes.
COPY --chown=docker:docker west.yml app/west.yml

USER docker

# Avoid reflog writes in ephemeral container repos; this prevents update-ref log path failures.
RUN git config --global core.logAllRefUpdates false

# Create Python virtual environment (as recommended by Zephyr documentation)
RUN python3 -m venv .venv
ENV PATH=/home/docker/zephyrproject/.venv/bin:$PATH
ENV VIRTUAL_ENV=/home/docker/zephyrproject/.venv

# Install west
RUN pip install --upgrade pip setuptools wheel && \
    pip install west

# Download Zephyr modules (cached as long as west.yml doesn't change)
RUN west init -l app && \
    west update --narrow -o=--depth=1 && \
    west zephyr-export

# Install Python requirements via west
RUN west packages pip --install

# Install Zephyr SDK toolchain only.
# Host tools are already provided via apt packages above.
ENV ZEPHYR_SDK_VERSION=0.17.4
ENV ZEPHYR_SDK_INSTALL_DIR=/home/docker/zephyr-sdk-${ZEPHYR_SDK_VERSION}
RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64_minimal.tar.xz -O /tmp/zephyr-sdk.tar.xz && \
    tar -xf /tmp/zephyr-sdk.tar.xz -C /home/docker && \
    ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh -t arm-zephyr-eabi && \
    rm -f /tmp/zephyr-sdk.tar.xz

# Copy application sources AFTER the SDK layers so they stay cached
COPY --chown=docker:docker src/           app/src/
COPY --chown=docker:docker proto/         app/proto/
COPY --chown=docker:docker boards/        app/boards/
COPY --chown=docker:docker CMakeLists.txt app/CMakeLists.txt
COPY --chown=docker:docker prj.conf       app/prj.conf

# Build firmware for the STM32 Nucleo-G070RB board
RUN west build -b nucleo_g070rb app --pristine

# ─── Stage 2: Runtime image ───────────────────────────────────────────────────
FROM debian:12-slim

# Install OpenOCD and tools for flash verification
RUN apt-get update && apt-get install -y \
    openocd \
    binutils \
    python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS

# Copy built firmware artifacts from the builder stage (no pre-built files needed)
COPY --from=builder /home/docker/zephyrproject/build/zephyr/zephyr.bin ./CybICS.bin
COPY --from=builder /home/docker/zephyrproject/build/zephyr/zephyr.elf ./CybICS.elf

# Copy OpenOCD configuration and flash script
COPY openocd_rpi.cfg ./
COPY openocd_virtual_server.py ./
COPY flash_if_needed.sh ./
RUN chmod +x /CybICS/flash_if_needed.sh /CybICS/openocd_virtual_server.py

# Expose OpenOCD ports
EXPOSE 3333 4444

# Check firmware version and flash only if needed, then start GDB server
CMD ["/CybICS/flash_if_needed.sh"]
