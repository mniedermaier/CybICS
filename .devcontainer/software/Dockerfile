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


RUN echo "ALL ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/nopasswd

RUN addgroup --gid 1000 docker \
    && adduser --uid 1000 --ingroup docker --home /home/docker --disabled-password --gecos "" docker \
    && echo 'docker:docker' | chpasswd \
    && usermod -a -G sudo docker

ENV HOME /home/docker

# RUN curl -fsSL https://get.docker.com | bash
RUN apt-get update && apt-get install -y \
    docker \
    docker-compose \
    docker-buildx \
    && rm -rf /var/lib/apt/lists/*

RUN USER=docker \
    && GROUP=docker \
    && curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - \
    && chown root:root /usr/local/bin/fixuid \
    && chmod 4755 /usr/local/bin/fixuid \
    && mkdir -p /etc/fixuid \
    && printf "user: $USER\ngroup: $GROUP\n" >/etc/fixuid/config.yml

USER docker:docker
ENTRYPOINT ["fixuid"]
