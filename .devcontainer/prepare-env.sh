#!/bin/bash

set -e

# Ensure default Docker builder is selected (required for devcontainers)
# cybicsbuilder2 is a docker-container builder used for cross-platform builds,
# but it doesn't have access to locally built images which breaks devcontainer UID updates
if ! docker buildx ls 2>/dev/null | grep -q '^default\*'; then
    echo "Switching to default Docker builder for devcontainer compatibility..."
    docker buildx use default
fi

DOCKER_ENV_DIR="$(pwd)/.docker.env"
mkdir -p "$DOCKER_ENV_DIR"

if [ ! -f .dev.env ]; then
  echo "DEVICE_IP=10.0.0.1" > .dev.env
  echo "DEVICE_USER=pi" >> .dev.env
fi

if [ ! -f ~/.gitconfig ]; then
  # prevent errors when mounting non-existing gitconfig (gets a directory and this will confuse git and west)
  touch ~/.gitconfig
fi

cat <<EOT >.env
HOST_UID=$(id -u)
HOST_GID=$(id -g)
DOCKER_ENV_DIR="$DOCKER_ENV_DIR"
CYBICS_ROOT="$(pwd)"
EOT

touch "$DOCKER_ENV_DIR"/.bash_history # persist bash history
cp .env .devcontainer/raspberry       # to also have some env values available in the docker-compose file
cp .env .devcontainer/stm32           # to also have some env values available in the docker-compose file
cp .env .devcontainer/virtual         # to also have some env values available in the docker-compose file
