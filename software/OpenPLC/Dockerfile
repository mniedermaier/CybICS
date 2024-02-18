FROM debian:12

RUN apt-get update && apt-get install -y \
    curl \
    gpg \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://archive.raspberrypi.com/debian/raspberrypi.gpg.key | gpg --dearmor -o /etc/apt/keyrings/raspberrypi.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/raspberrypi.gpg] http://archive.raspberrypi.com/debian/ bookworm main" >/etc/apt/sources.list.d/raspi.list \
    && apt-get update && apt-get install -y \
    pigpio \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /CybICS/ \
    && cd /CybICS \
    && git clone https://github.com/thiagoralves/OpenPLC_v3.git \
    && git -C /CybICS/OpenPLC_v3/ checkout 6621e30830e256dd271a5cf60e430164e080e7b0

COPY openplc.patch /tmp/openplc.patch
RUN git -C /CybICS/OpenPLC_v3/ apply /tmp/openplc.patch

WORKDIR /CybICS/OpenPLC_v3/
COPY openplc.db webserver/openplc.db
COPY cybICS.st webserver/st_files/724870.st
RUN export GNUMAKEFLAGS=-j$(nproc --all) \
    && alias make='make -j$(nproc --all)' \
    && ./install.sh docker

WORKDIR /CybICS/OpenPLC_v3/webserver
RUN ./scripts/change_hardware_layer.sh rpi
RUN ./scripts/compile_program.sh 724870.st

EXPOSE 8080
EXPOSE 502
CMD rm -f /var/run/pigpio.pid && /CybICS/OpenPLC_v3/start_openplc.sh
