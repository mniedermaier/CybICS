FROM ubuntu:22.04

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
    locales \
    bc \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN python3 -m pip install pymodbus flask

# RUN curl -fsSL https://get.docker.com | bash

RUN apt-get update && apt-get install -y \
    docker \
    docker-compose \
    docker-buildx \
    && rm -rf /var/lib/apt/lists/*

RUN echo "ALL ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/nopasswd

RUN addgroup --gid 1000 devuser \
    && adduser --disabled-password --gecos "" --uid 1000 --gid 1000 devuser \
    && echo 'devuser:devuser' | chpasswd \
    && usermod -a -G sudo,docker devuser
ENV HOME /home/devuser
RUN export PATH="/home/devuser/.local/bin:$PATH"

USER devuser
RUN mkdir /home/devuser/.docker
