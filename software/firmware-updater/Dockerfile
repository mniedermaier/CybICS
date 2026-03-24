FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openocd \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/cybics/update-service

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY update_daemon.py .
COPY config.yaml .
COPY generate_mac.py .
COPY flash_firmware.sh .
COPY entrypoint.sh .
RUN chmod +x flash_firmware.sh entrypoint.sh

# Persistent directories (override via volume mounts)
RUN mkdir -p /opt/cybics/firmware /opt/cybics/keys /opt/cybics/logs

ENTRYPOINT ["/opt/cybics/update-service/entrypoint.sh"]
