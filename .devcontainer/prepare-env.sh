#!/bin/bash

set -e

DOCKER_ENV_DIR="$(pwd)/.docker.env"
mkdir -p "$DOCKER_ENV_DIR"

touch .dev.env

cat <<EOT >.env
HOST_UID=$(id -u)
HOST_GID=$(id -g)
DOCKER_ENV_DIR="$DOCKER_ENV_DIR"
EOT

touch "$DOCKER_ENV_DIR"/.bash_history # persist bash history
cp .env .devcontainer/software        # to also have some env values available in the docker-compose file
cp .env .devcontainer/stm32           # to also have some env values available in the docker-compose file
