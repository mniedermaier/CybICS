FROM debian:12-slim

RUN apt-get update && apt-get install -y \
    libstdc++6 \
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
CMD /CybICS/OpenPLC_v3/start_openplc.sh
