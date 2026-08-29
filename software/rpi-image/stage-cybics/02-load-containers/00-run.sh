#!/bin/bash -e

# Copy pre-built container tarballs to the image
# These tarballs are created by the build-image.sh script before pi-gen runs

# Look for containers in the stage directory (more reliable than STAGE_WORK_DIR)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_DIR="${SCRIPT_DIR}/containers"

if [ -d "${CONTAINER_DIR}" ] && ls "${CONTAINER_DIR}"/*.tar 1>/dev/null 2>&1; then
    install -d "${ROOTFS_DIR}/opt/cybics/images"
    cp "${CONTAINER_DIR}"/*.tar "${ROOTFS_DIR}/opt/cybics/images/"
    echo "Copied container images to /opt/cybics/images/"
    ls -lh "${ROOTFS_DIR}/opt/cybics/images/"
else
    echo "Warning: No container images found at ${CONTAINER_DIR}"
    echo "The image will need to pull containers on first boot."
fi

# Copy docker-compose.yaml for local images
install -d "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/CybICS"
if [ -f "files/docker-compose.yaml" ]; then
    cp files/docker-compose.yaml "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/CybICS/"
fi

# Set ownership
chown -R 1000:1000 "${ROOTFS_DIR}/home/${FIRST_USER_NAME}/CybICS"
