FROM debian:12-slim as build

RUN apt-get update && apt-get install -y \
    make \
    gcc-arm-none-eabi \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /CybICS
COPY ./ ./
RUN make -j$(nproc --all)

FROM debian:12-slim
WORKDIR /CybICS
RUN apt-get update && apt-get install -y \
    openocd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /CybICS/build/CybICS.bin/ ./CybICS.bin
COPY ./openocd_rpi.cfg ./

EXPOSE 3333
EXPOSE 4444
CMD openocd -f /CybICS/openocd_rpi.cfg -c "program CybICS.bin verify reset exit 0x08000000" \
    && sleep infinity
