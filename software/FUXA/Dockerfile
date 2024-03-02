FROM debian:12

RUN apt-get update && apt-get install -y \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g --unsafe-perm @frangoteam/fuxa

WORKDIR /CybICS
COPY ./ ./

RUN set -e && fuxa & \
    while ! curl -X POST -H "Content-Type: application/json" -d @/CybICS/fuxa-project.json http://localhost:1881/api/project; do sleep 1; done && \
    curl -X POST -H "Content-Type: application/json" -d @/CybICS/add-user.json http://localhost:1881/api/users && \
    curl -X POST -H "Content-Type: application/json" -d @/CybICS/settings.json http://localhost:1881/api/settings

EXPOSE 1881
CMD fuxa
