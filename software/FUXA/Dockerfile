FROM node:20-alpine

# Install dependencies for FUXA (including build tools for native modules)
RUN apk add --no-cache \
    curl \
    unixodbc-dev \
    python3 \
    py3-setuptools \
    make \
    g++

# Install FUXA globally
RUN npm install -g --unsafe-perm @frangoteam/fuxa@1.2.6 && \
    npm cache clean --force && \
    apk del python3 py3-setuptools make g++

WORKDIR /CybICS
COPY ./ ./

# Pre-configure FUXA with project and settings
RUN set -e && fuxa & \
    while ! curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/fuxa-project.json http://localhost:1881/api/project; do sleep 1; done && \
    curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/add-user-viewer.json http://localhost:1881/api/users && \
    curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/add-user-operator.json http://localhost:1881/api/users && \
    curl -f -X POST -H "Content-Type: application/json" -d @/CybICS/settings.json http://localhost:1881/api/settings

EXPOSE 1881
CMD ["fuxa"]
