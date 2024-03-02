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

RUN addgroup --gid 1000 docker \
    && adduser --uid 1000 --ingroup docker --home /home/docker --disabled-password --gecos "" docker \
    && echo 'docker:docker' | chpasswd \
    && usermod -a -G sudo docker

RUN USER=docker \
    && GROUP=docker \
    && curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - \
    && chown root:root /usr/local/bin/fixuid \
    && chmod 4755 /usr/local/bin/fixuid \
    && mkdir -p /etc/fixuid \
    && printf "user: $USER\ngroup: $GROUP\n" >/etc/fixuid/config.yml

ENV HOME /home/docker

USER docker:docker
ENTRYPOINT ["fixuid"]
