FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

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

# Create user
RUN addgroup --gid 1000 docker \
    && adduser --uid 1000 --ingroup docker --home /home/docker --disabled-password --gecos "" docker \
    && echo 'docker:docker' | chpasswd \
    && usermod -a -G sudo docker

# Copy west manifest for minimal Zephyr workspace
COPY --chown=docker:docker software/stm32/west.yml /home/docker/zephyrproject/app/west.yml

# Pre-bake Zephyr workspace (as docker user for correct permissions)
USER docker
WORKDIR /home/docker/zephyrproject

# Upgrade pip and pin setuptools/setuptools_scm to avoid version backtracking
RUN pip3 install --user --upgrade pip setuptools wheel setuptools_scm

# Initialize workspace using manifest (downloads only required modules)
RUN west init -l app && \
    west update --narrow -o=--depth=1

# Install Python requirements (needed for west sdk install)
RUN pip3 install --user --no-build-isolation -r zephyr/scripts/requirements.txt

# Install Zephyr SDK using west (only ARM toolchain)
RUN west sdk install -t arm-zephyr-eabi

# Set environment variables
ENV ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ENV ZEPHYR_BASE=/home/docker/zephyrproject/zephyr
ENV ZEPHYR_SDK_INSTALL_DIR=/home/docker/zephyr-sdk-0.17.4
ENV PATH=/home/docker/zephyr-sdk-0.17.4/arm-zephyr-eabi/bin:/home/docker/.local/bin:$PATH

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
