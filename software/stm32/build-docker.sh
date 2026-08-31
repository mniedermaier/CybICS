#!/bin/bash
# Build script for STM32 Zephyr firmware Docker image

set -e

echo "Building CybICS STM32 Zephyr firmware Docker image..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Build the Docker image
docker build -t localhost:5050/cybics-stm32:latest .

echo ""
echo "✓ Docker image built successfully!"
echo ""
echo "To push to local registry:"
echo "  docker push localhost:5050/cybics-stm32:latest"
echo ""
echo "To run the container and flash the STM32:"
echo "  docker run --privileged -p 3333:3333 localhost:5050/cybics-stm32:latest"
echo ""
echo "Or use docker-compose from the software directory:"
echo "  cd ../.. && docker-compose up stm32"
