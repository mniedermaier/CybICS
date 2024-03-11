FROM debian:12

RUN apt-get update && apt-get install -y \
    curl \
    gpg \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://archive.raspberrypi.com/debian/raspberrypi.gpg.key | gpg --dearmor -o /etc/apt/keyrings/raspberrypi.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/raspberrypi.gpg] http://archive.raspberrypi.com/debian/ bookworm main" >/etc/apt/sources.list.d/raspi.list \
    && apt-get update && apt-get install -y \
    pigpio \
    socat \
    && rm -rf /var/lib/apt/lists/*

COPY ./OpenPLC_v3/ /CybICS/OpenPLC_v3/
WORKDIR /CybICS/OpenPLC_v3/
RUN export GNUMAKEFLAGS=-j$(nproc --all) \
    && alias make='make -j$(nproc --all)' \
    && ./install.sh docker

# copy files after compile the main part to reduce re-compile time on changes on cybICS.st
WORKDIR /CybICS/OpenPLC_v3/webserver
COPY cybICS.st st_files/724870.st
COPY openplc.db openplc.db
RUN ./scripts/compile_program.sh 724870.st

EXPOSE 8080
EXPOSE 502
EXPOSE 44818
EXPOSE 20000
CMD socat TCP-LISTEN:8888,reuseaddr,fork UNIX-CLIENT:/var/run/pigpiod.sock & /CybICS/OpenPLC_v3/start_openplc.sh
