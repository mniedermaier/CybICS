FROM python:3.10.15-slim

RUN apt-get update && apt-get install -y \
    network-manager \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p pics
COPY app.py ./
COPY ctf_config.json ./
COPY pics/ pics/
COPY templates/ templates/

CMD [ "python", "./app.py" ]
