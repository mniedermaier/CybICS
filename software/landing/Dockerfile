FROM python:3.10.15-slim

RUN apt-get update && apt-get install -y \
    network-manager \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /CybICS
COPY software/landing/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p pics
COPY software/landing/app.py ./
COPY software/landing/ctf_config.json ./
COPY software/landing/pics/ pics/
COPY software/landing/templates/ templates/
COPY training/ training/

CMD [ "python", "./app.py" ]
