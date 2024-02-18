FROM debian:12

RUN apt-get update && apt-get install -y \
    npm \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g --unsafe-perm @frangoteam/fuxa

EXPOSE 1881
CMD fuxa
