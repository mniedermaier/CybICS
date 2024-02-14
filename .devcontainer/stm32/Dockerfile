FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    gcc-arm-none-eabi \
    binutils-arm-none-eabi \
    libnewlib-arm-none-eabi \
    gdb-multiarch \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/gdb-multiarch /usr/bin/arm-none-eabi-gdb

RUN apt-get update && apt-get install -y \
    sudo \
    git \
    tig \
    bash-completion \
    python3 \
    python3-pip \
    sqlite3 \
    vim \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install pymodbus flask

RUN addgroup --gid 1000 devuser \
    && adduser --disabled-password --gecos "" --uid 1000 --gid 1000 devuser \
    && echo 'devuser:devuser' | chpasswd \
    && usermod -a -G sudo devuser
ENV HOME /home/devuser
RUN export PATH="/home/devuser/.local/bin:$PATH"

USER devuser
