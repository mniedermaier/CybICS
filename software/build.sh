#!/bin/bash

set -e
cd "$(dirname "$0")"

name=cybicsbuilder
docker buildx ls | grep -q $name || docker buildx create --driver-opt network=host --use --config config.toml --name $name
docker buildx inspect --bootstrap

docker buildx build --platform linux/arm64 -t localhost:5000/cybics-hwio-rpi:latest --push ./hwio-rpi
docker buildx build --platform linux/arm64 -t localhost:5000/cybics-openplc:latest --push ./OpenPLC
docker buildx build --platform linux/arm64 -t localhost:5000/cybics-opcua:latest --push ./opcua
docker buildx build --platform linux/arm64 -t localhost:5000/cybics-fuxa:latest --push ./FUXA
docker buildx build --platform linux/arm64 -t localhost:5000/cybics-stm32:latest --push ./stm32
