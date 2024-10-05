FROM python:3-slim

RUN apt-get update && apt-get install -y \
    network-manager \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY hardwareIO.py ./

CMD [ "python", "./hardwareIO.py" ]
