FROM debian:12

RUN apt-get update && apt-get install -y \
    openocd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS
COPY openocd_rpi.cfg ./
EXPOSE 3333
EXPOSE 4444
CMD openocd -f /home/pi/gits/CybICS/software/stm32/openocd_rpi.cfg
