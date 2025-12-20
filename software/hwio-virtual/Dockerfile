FROM python:3.12-slim

# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    network-manager \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir --verbose -r requirements.txt
RUN mkdir -p pics
COPY hardwareAbstraction.py ./
COPY pics/CybICS_logo.png pics/CybICS_logo.png
COPY pics/favicon.ico pics/favicon.ico
COPY pics/pcb.png pics/pcb.png

CMD [ "python", "-u", "./hardwareAbstraction.py" ]
