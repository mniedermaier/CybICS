FROM debian:12-slim

COPY ./OpenPLC_v3/ /CybICS/OpenPLC_v3/
WORKDIR /CybICS/OpenPLC_v3/
RUN export GNUMAKEFLAGS=-j$(nproc --all) \
    && alias make='make -j$(nproc --all)' \
    && ./install.sh docker

# copy files after compile the main part to reduce re-compile time on changes on cybICS.st
WORKDIR /CybICS/OpenPLC_v3/webserver
COPY cybICS.st st_files/424345.st
COPY openplc.db openplc.db
RUN ./scripts/compile_program.sh 424345.st

EXPOSE 8080
EXPOSE 502
EXPOSE 44818
EXPOSE 20000
EXPOSE 102
CMD ["/CybICS/OpenPLC_v3/start_openplc.sh"]
