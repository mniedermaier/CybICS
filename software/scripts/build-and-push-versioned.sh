#!/bin/bash

# Script to build and push Docker images with proper versioning
# Usage: ./build-and-push-versioned.sh [--push] [--tag <custom-tag>]

set -e

# Parse arguments
PUSH=false
CUSTOM_TAG=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --push)
      PUSH=true
      shift
      ;;
    --tag)
      CUSTOM_TAG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--push] [--tag <custom-tag>]"
      exit 1
      ;;
  esac
done

# Get version information
SHA_SHORT=$(git rev-parse --short HEAD)
GIT_TAG=$(git describe --exact-match --tags 2>/dev/null || echo "")

# Determine tags to apply
TAGS=("latest" "$SHA_SHORT")

if [ -n "$GIT_TAG" ]; then
  VERSION_TAG=${GIT_TAG#v}
  TAGS+=("$VERSION_TAG")
  echo "Building release version: $GIT_TAG"
elif [ -n "$CUSTOM_TAG" ]; then
  TAGS+=("$CUSTOM_TAG")
  echo "Building with custom tag: $CUSTOM_TAG"
else
  echo "Building development version"
fi

echo "Tags to apply: ${TAGS[*]}"

# Helper function to build and optionally push with multiple tags
build_and_push() {
  local IMAGE_NAME=$1
  local CONTEXT=$2
  local DOCKERFILE=$3

  echo ""
  echo "========================================"
  echo "Building: ${IMAGE_NAME}"
  echo "Context: ${CONTEXT}"
  echo "Dockerfile: ${DOCKERFILE}"
  echo "========================================"

  # Build tag arguments
  TAG_ARGS=""
  for tag in "${TAGS[@]}"; do
    TAG_ARGS="$TAG_ARGS -t ${IMAGE_NAME}:${tag}"
    echo "  - ${IMAGE_NAME}:${tag}"
  done

  # Build command
  BUILD_CMD="docker buildx build --platform linux/amd64 ${TAG_ARGS}"

  if [ "$PUSH" = true ]; then
    BUILD_CMD="$BUILD_CMD --push"
    echo "Building and pushing..."
  else
    BUILD_CMD="$BUILD_CMD --load"
    echo "Building locally (not pushing)..."
  fi

  BUILD_CMD="$BUILD_CMD -f ${DOCKERFILE} ${CONTEXT}"

  # Execute build
  eval $BUILD_CMD

  echo "✓ Completed: ${IMAGE_NAME}"
}

# Ensure we're in the repository root
cd "$(git rev-parse --show-toplevel)"

# Ensure environment files are created
if [ -f .devcontainer/prepare-env.sh ]; then
  echo "Creating environment files..."
  .devcontainer/prepare-env.sh
fi

# Create or use existing buildx builder
if ! docker buildx inspect multiarch-builder &>/dev/null; then
  echo "Creating buildx builder: multiarch-builder"
  docker buildx create --name multiarch-builder --use
else
  echo "Using existing buildx builder: multiarch-builder"
  docker buildx use multiarch-builder
fi

echo ""
echo "========================================"
echo "Starting build process"
echo "========================================"

# Build and push all images
build_and_push "mniedermaier1337/cybics-attack-machine" "software/attack-machine" "software/attack-machine/Dockerfile"
build_and_push "mniedermaier1337/cybicsopenplc" "software/OpenPLC" "software/OpenPLC/Dockerfile"
build_and_push "mniedermaier1337/cybicsopcua" "software/opcua" "software/opcua/Dockerfile"
build_and_push "mniedermaier1337/cybicss7com" "software/s7com" "software/s7com/Dockerfile"
build_and_push "mniedermaier1337/cybicsfuxa" "software/FUXA" "software/FUXA/Dockerfile"
build_and_push "mniedermaier1337/cybicshwio" "software/hwio-virtual" "software/hwio-virtual/Dockerfile"
build_and_push "mniedermaier1337/landing" "." "software/landing/Dockerfile"
build_and_push "mniedermaier1337/cybics-engineeringws" "software" "software/engineeringWS/Dockerfile"

echo ""
echo "========================================"
echo "✓ All builds completed successfully!"
echo "========================================"
echo ""
echo "Images tagged with: ${TAGS[*]}"

if [ "$PUSH" = true ]; then
  echo "Images have been pushed to Docker Hub"
else
  echo ""
  echo "To push these images to Docker Hub, run:"
  echo "  $0 --push"
fi
