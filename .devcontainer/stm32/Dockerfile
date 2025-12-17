FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Zephyr and SDK versions
ARG ZEPHYR_VERSION=v4.3.0
ARG ZEPHYR_SDK_VERSION=0.17.4

# Install base dependencies and Zephyr requirements in one layer
RUN apt-get update && apt-get install -y \
    sudo \
    git \
    tig \
    bash-completion \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-tk \
    python3-wheel \
    vim \
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
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install west (Zephyr meta-tool)
RUN pip3 install --no-cache-dir west

# Install Zephyr SDK
ARG ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk
RUN wget -q https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${ZEPHYR_SDK_VERSION}/zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz && \
    mkdir -p ${ZEPHYR_SDK_INSTALL_DIR} && \
    tar -xf zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz -C ${ZEPHYR_SDK_INSTALL_DIR} --strip-components=1 && \
    rm zephyr-sdk-${ZEPHYR_SDK_VERSION}_linux-x86_64.tar.xz && \
    ${ZEPHYR_SDK_INSTALL_DIR}/setup.sh -t arm-zephyr-eabi -h -c

# Create user
RUN addgroup --gid 1000 docker \
    && adduser --uid 1000 --ingroup docker --home /home/docker --disabled-password --gecos "" docker \
    && echo 'docker:docker' | chpasswd \
    && usermod -a -G sudo docker

# Pre-bake Zephyr workspace (as docker user for correct permissions)
USER docker
WORKDIR /home/docker

# Upgrade pip and pin setuptools to avoid version backtracking during requirements install
RUN pip3 install --user --upgrade pip setuptools wheel

RUN west init -m https://github.com/zephyrproject-rtos/zephyr --mr ${ZEPHYR_VERSION} zephyrproject && \
    cd zephyrproject && \
    west update && \
    west zephyr-export && \
    pip3 install --user --no-build-isolation -r zephyr/scripts/requirements.txt

# Set environment variables
ENV ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_BASE=/home/docker/zephyrproject/zephyr
ENV PATH=/home/docker/.local/bin:$PATH

# Switch back to root for fixuid setup
USER root

RUN curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - \
    && chown root:root /usr/local/bin/fixuid \
    && chmod 4755 /usr/local/bin/fixuid \
    && mkdir -p /etc/fixuid \
    && printf "user: docker\ngroup: docker\n" >/etc/fixuid/config.yml

# Create docker-init.sh
RUN echo '#!/bin/sh\nfixuid\nexec "$@"' > /usr/local/share/docker-init.sh \
    && chmod +x /usr/local/share/docker-init.sh

ENV HOME=/home/docker
USER docker:docker

ENTRYPOINT [ "/usr/local/share/docker-init.sh" ]
CMD [ "sleep", "infinity" ]
