FROM debian:12-slim

RUN apt-get update && apt-get install -y \
    npm \
    curl \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g --unsafe-perm @frangoteam/fuxa

WORKDIR /CybICS
COPY ./ ./

RUN set -e && fuxa & \
    while ! curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/fuxa-project.json http://localhost:1881/api/project; do sleep 1; done && \
    curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/add-user-viewer.json http://localhost:1881/api/users && \
    curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/add-user-operator.json http://localhost:1881/api/users && \
    curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/settings.json http://localhost:1881/api/settings

EXPOSE 1881
CMD fuxa