FROM python:3-slim

RUN apt-get update && apt-get install -y \
    network-manager \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY s7com.py ./

CMD [ "python", "./s7com.py" ]
