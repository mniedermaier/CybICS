#!/bin/bash

set -e
cd "$(dirname "$0")"

# Output directory for tarballs (can be set externally)
TARBALL_DIR="${TARBALL_DIR:-}"

# Ensure we always switch back to default builder, even on error/interrupt
trap 'docker buildx use default' EXIT

name=cybicsbuilder2
docker buildx ls | grep -q $name && docker buildx use $name
docker buildx ls | grep -q $name || docker buildx create  --use --config config.toml --name $name
docker buildx inspect --bootstrap

docker compose -f ../.devcontainer/stm32/docker-compose.yml build
docker compose -f ../.devcontainer/stm32/docker-compose.yml run --rm dev scripts/build.sh

# Build function that handles both registry push and optional tarball export
build_image() {
    local name="$1"
    local context="$2"
    local dockerfile="${3:-}"

    local registry_tag="172.17.0.1:5050/${name}:latest"
    local local_tag="${name}:latest"

    if [ -n "$TARBALL_DIR" ]; then
        # Export directly to tarball with LOCAL name (for offline use on Pi)
        echo "Building ${name} with tarball export..."
        if [ -n "$dockerfile" ]; then
            docker buildx build --platform linux/arm64 -t "$local_tag" --output "type=docker,dest=${TARBALL_DIR}/${name}.tar" -f "$dockerfile" "$context"
        else
            docker buildx build --platform linux/arm64 -t "$local_tag" --output "type=docker,dest=${TARBALL_DIR}/${name}.tar" "$context"
        fi
        # Also push to registry for caching (with registry tag)
        if [ -n "$dockerfile" ]; then
            docker buildx build --platform linux/arm64 -t "$registry_tag" --push -f "$dockerfile" "$context"
        else
            docker buildx build --platform linux/arm64 -t "$registry_tag" --push "$context"
        fi
    else
        # Just push to registry
        if [ -n "$dockerfile" ]; then
            docker buildx build --platform linux/arm64 -t "$registry_tag" --push -f "$dockerfile" "$context"
        else
            docker buildx build --platform linux/arm64 -t "$registry_tag" --push "$context"
        fi
    fi
}

build_image "cybics-hwio-raspberry" "./hwio-raspberry"
build_image "cybics-openplc" "./OpenPLC"
build_image "cybics-opcua" "./opcua"
build_image "cybics-s7com" "./s7com"
build_image "cybics-fuxa" "./FUXA"
build_image "cybics-stm32" "./stm32"
# Build landing service from root context
build_image "cybics-landing" ".." "./landing/Dockerfile"

# Note: Builder automatically switches back to default on EXIT via trap