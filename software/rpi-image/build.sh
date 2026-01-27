#!/bin/bash
#
# CybICS Raspberry Pi Image Builder
#
# This script builds a complete 64-bit Raspberry Pi image with all CybICS
# containers pre-loaded. The resulting image is ready to use on first boot.
#
# Requirements:
# - Docker with buildx support
# - ~20GB free disk space
# - Internet connection for initial build
#
# Usage: ./build.sh [--skip-containers]
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOFTWARE_DIR="$(dirname "$SCRIPT_DIR")"
GIT_ROOT="$(dirname "$SOFTWARE_DIR")"
PIGEN_DIR="$SCRIPT_DIR/pi-gen"
DEPLOY_DIR="$SCRIPT_DIR/deploy"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Parse arguments
SKIP_CONTAINERS=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-containers)
            SKIP_CONTAINERS=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--skip-containers]"
            echo ""
            echo "Options:"
            echo "  --skip-containers  Skip building ARM64 containers (use existing)"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
print_step "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker buildx version &> /dev/null; then
    print_error "Docker buildx is not available. Please update Docker."
    exit 1
fi

if [ ! -d "$PIGEN_DIR" ]; then
    print_error "Pi-gen submodule not found at $PIGEN_DIR"
    echo "Run: git submodule update --init --recursive"
    exit 1
fi

# Ensure local Docker registry is running (needed for ARM64 cross-builds)
REGISTRY="172.17.0.1:5050"
REGISTRY_NAME="pigen-registry"

if ! curl -s "http://${REGISTRY}/v2/" &>/dev/null; then
    print_step "Starting local Docker registry..."
    docker rm -f "$REGISTRY_NAME" 2>/dev/null || true
    docker run -d -p 5050:5000 --restart=always --name "$REGISTRY_NAME" registry:2
    # Wait for registry to be ready
    for i in {1..10}; do
        if curl -s "http://${REGISTRY}/v2/" &>/dev/null; then
            break
        fi
        sleep 1
    done
    if ! curl -s "http://${REGISTRY}/v2/" &>/dev/null; then
        print_error "Failed to start local Docker registry"
        exit 1
    fi
fi

# Create work directories
print_step "Creating work directories..."
mkdir -p "$PIGEN_DIR/work/stage-cybics/containers"
mkdir -p "$DEPLOY_DIR"

# Container tarball output directory
TARBALL_DIR="$PIGEN_DIR/work/stage-cybics/containers"

CONTAINERS=(
    "cybics-hwio-raspberry"
    "cybics-openplc"
    "cybics-opcua"
    "cybics-s7com"
    "cybics-fuxa"
    "cybics-landing"
    "cybics-stm32"
)

# Step 1: Build ARM64 containers (unless skipped)
if [ "$SKIP_CONTAINERS" = false ]; then
    print_step "Building ARM64 Docker containers and exporting tarballs..."
    TARBALL_DIR="$TARBALL_DIR" "$SOFTWARE_DIR/build.sh"
else
    print_warning "Skipping container build (--skip-containers)"
fi

# Step 2: Verify container tarballs exist
print_step "Verifying container tarballs..."

MISSING=0
for container in "${CONTAINERS[@]}"; do
    TARBALL="$TARBALL_DIR/${container}.tar"
    if [ -f "$TARBALL" ]; then
        echo "  Found: ${container}.tar ($(du -h "$TARBALL" | cut -f1))"
    else
        print_warning "Missing: ${container}.tar"
        MISSING=$((MISSING + 1))
    fi
done

if [ "$MISSING" -gt 0 ] && [ "$SKIP_CONTAINERS" = false ]; then
    print_error "Some container tarballs are missing. Build may have failed."
    exit 1
fi

# Step 3: Copy configuration to pi-gen
print_step "Setting up pi-gen configuration..."
cp "$SCRIPT_DIR/config" "$PIGEN_DIR/config"

# Remove old stage-cybics if it exists
rm -rf "$PIGEN_DIR/stage-cybics"

# Copy our custom stage
cp -r "$SCRIPT_DIR/stage-cybics" "$PIGEN_DIR/"

# Copy container tarballs INTO the stage directory (so they're available inside pi-gen Docker)
print_step "Copying container tarballs to stage directory..."
mkdir -p "$PIGEN_DIR/stage-cybics/02-load-containers/containers"
cp "$TARBALL_DIR"/*.tar "$PIGEN_DIR/stage-cybics/02-load-containers/containers/"
ls -lh "$PIGEN_DIR/stage-cybics/02-load-containers/containers/"

# Make scripts executable
find "$PIGEN_DIR/stage-cybics" -name "*.sh" -exec chmod +x {} \;

# Step 4: Skip unused stages
print_step "Configuring pi-gen stages..."
for stage in stage3 stage4 stage5; do
    touch "$PIGEN_DIR/$stage/SKIP"
done
touch "$PIGEN_DIR/stage4/SKIP_IMAGES"
touch "$PIGEN_DIR/stage5/SKIP_IMAGES"

# Step 5: Run pi-gen build
print_step "Building Raspberry Pi image (this will take a while)..."
cd "$PIGEN_DIR"

# Clean previous build artifacts if they exist
if [ -d "work" ] && [ -d "work/stage-cybics" ]; then
    # Keep our containers but clean other artifacts
    print_step "Cleaning previous build (keeping containers)..."
fi

# Run the Docker-based build
./build-docker.sh

# Step 6: Copy output
print_step "Copying build output..."
if ls "$PIGEN_DIR/deploy/"*.img.xz 1> /dev/null 2>&1; then
    cp "$PIGEN_DIR/deploy/"*.img.xz "$DEPLOY_DIR/"
    echo ""
    print_step "Build complete!"
    echo ""
    echo "Image files are available in: $DEPLOY_DIR/"
    ls -lh "$DEPLOY_DIR/"*.img.xz 2>/dev/null || true
    echo ""
    echo "To flash to an SD card:"
    echo "  xzcat software/rpi-image/deploy/CybICS-*.img.xz | sudo dd of=/dev/sdX bs=4M status=progress"
    echo ""
else
    print_error "No image files found in pi-gen/deploy/"
    exit 1
fi
