#!/bin/bash

set -e
cd "$(dirname "$0")"

name=cybicsbuilder2
docker buildx ls | grep -q $name && docker buildx use $name
docker buildx ls | grep -q $name || docker buildx create  --use --config config.toml --name $name
docker buildx inspect --bootstrap

docker compose -f ../.devcontainer/stm32/docker-compose.yml build
docker compose -f ../.devcontainer/stm32/docker-compose.yml run --rm dev scripts/build.sh

docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-hwio-raspberry:latest --push ./hwio-raspberry
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-openplc:latest --push ./OpenPLC
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-opcua:latest --push ./opcua
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-s7com:latest --push ./s7com
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-fuxa:latest --push ./FUXA
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-stm32:latest --push ./stm32
# Build landing service from root context
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-landing:latest --push -f ./landing/Dockerfile ..

# Switch back to default builder to avoid breaking devcontainers
docker buildx use default