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

# Create Python virtual environment (as recommended by Zephyr documentation)
RUN python3 -m venv .venv

# Set PATH to use virtual environment
ENV PATH=/home/docker/zephyrproject/.venv/bin:$PATH
ENV VIRTUAL_ENV=/home/docker/zephyrproject/.venv

# Install west and pre-pin packages in virtual environment
RUN pip install --upgrade pip setuptools wheel && \
    pip install west

# Initialize workspace using manifest (downloads only required modules)
RUN west init -l app && \
    west update --narrow -o=--depth=1 && \
    west zephyr-export

# Install Python requirements using west (recommended method)
RUN west packages pip --install

# Install the Zephyr SDK (ARM toolchain only).
#
# Fetched straight from the release URL instead of via 'west sdk install',
# which queries the GitHub API unauthenticated.  Anonymous API calls are capped
# at 60/hour per IP, and on shared CI runners that budget is regularly spent by
# unrelated jobs: 17 of the last 100 nightly devContainer runs failed right
# here with HTTP 403 "API rate limit exceeded", independently of our own
# activity.  Release asset downloads do not count against that budget.
#
# The version is read from the Zephyr tree so it follows software/stm32/west.yml
# rather than drifting; .github/workflows/buildTest.yml installs the same SDK
# the same way.
RUN set -eu; \
    SDK_VERSION="$(cat /home/docker/zephyrproject/zephyr/SDK_VERSION)"; \
    BASE="https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${SDK_VERSION}"; \
    cd /home/docker; \
    wget -q "${BASE}/zephyr-sdk-${SDK_VERSION}_linux-x86_64_minimal.tar.xz"; \
    tar xf "zephyr-sdk-${SDK_VERSION}_linux-x86_64_minimal.tar.xz"; \
    rm "zephyr-sdk-${SDK_VERSION}_linux-x86_64_minimal.tar.xz"; \
    cd "zephyr-sdk-${SDK_VERSION}"; \
    wget -q "${BASE}/toolchain_linux-x86_64_arm-zephyr-eabi.tar.xz"; \
    tar xf toolchain_linux-x86_64_arm-zephyr-eabi.tar.xz; \
    rm toolchain_linux-x86_64_arm-zephyr-eabi.tar.xz; \
    ./setup.sh -t arm-zephyr-eabi -h -c

# Switch back to root for fixuid setup
USER root

RUN curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - \
    && chown root:root /usr/local/bin/fixuid \
    && chmod 4755 /usr/local/bin/fixuid \
    && mkdir -p /etc/fixuid \
    && printf "user: docker\ngroup: docker\n" >/etc/fixuid/config.yml

# Create docker-init.sh
RUN echo '#!/bin/sh\nfixuid -q\nexec "$@"' > /usr/local/share/docker-init.sh \
    && chmod +x /usr/local/share/docker-init.sh

ENV HOME=/home/docker
USER docker:docker
WORKDIR /home/docker/zephyrproject/app

ENTRYPOINT [ "/usr/local/share/docker-init.sh" ]
CMD [ "sleep", "infinity" ]
