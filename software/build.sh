#!/bin/bash

set -e
cd "$(dirname "$0")"

name=cybicsbuilder
docker buildx ls | grep -q $name || docker buildx create --driver-opt network=host --use --config config.toml --name $name
docker buildx inspect --bootstrap

docker buildx build --platform linux/arm64 -t localhost:5000/cybics-readi2c:latest --push ./scripts
docker buildx build --platform linux/arm64 -t localhost:5000/cybics-openplc:latest --push ./OpenPLC
