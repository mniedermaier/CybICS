FROM debian:12

RUN apt-get update && apt-get install -y \
    openocd \
    make \
    gcc-arm-none-eabi \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS
COPY ./ ./
RUN make -j$(nproc --all)
EXPOSE 3333
EXPOSE 4444
CMD openocd -f /CybICS/openocd_rpi.cfg -c "program build/CybICS.bin verify reset exit 0x08000000" \
    && openocd -f /CybICS/openocd_rpi.cfg
