FROM python:3

RUN apt-get update && apt-get install -y \
    network-manager \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY opcua.py ./

CMD [ "python", "./opcua.py" ]
