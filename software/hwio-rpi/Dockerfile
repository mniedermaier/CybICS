FROM python:3

RUN apt-get update && apt-get install -y \
    network-manager \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY readI2Cpi.py ./

CMD [ "python", "./readI2Cpi.py" ]
