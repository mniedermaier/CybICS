#!/bin/bash -e

# Create first-boot service to load Docker images from tarballs
# This service runs once on first boot, loads all images, then disables itself

cat > /etc/systemd/system/cybics-first-boot.service << 'EOF'
[Unit]
Description=CybICS First Boot - Load Docker Images
After=docker.service
Requires=docker.service
ConditionPathExists=/opt/cybics/images

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'for img in /opt/cybics/images/*.tar; do echo "Loading $img..."; docker load -i "$img"; done'
ExecStartPost=/bin/rm -rf /opt/cybics/images
ExecStartPost=/bin/systemctl disable cybics-first-boot.service
RemainAfterExit=yes
TimeoutStartSec=600

[Install]
WantedBy=multi-user.target
EOF

systemctl enable cybics-first-boot.service

# Create CybICS container startup service
cat > /etc/systemd/system/cybics.service << 'EOF'
[Unit]
Description=CybICS Docker Containers
After=docker.service cybics-first-boot.service network-online.target
Requires=docker.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/CybICS
ExecStart=/usr/bin/docker compose up -d --remove-orphans
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF

systemctl enable cybics.service
