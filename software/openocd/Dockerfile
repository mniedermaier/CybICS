FROM debian:12

RUN apt-get update && apt-get install -y \
    openocd \
    && rm -rf /var/lib/apt/lists/*

EXPOSE 8080
EXPOSE 502
CMD open
