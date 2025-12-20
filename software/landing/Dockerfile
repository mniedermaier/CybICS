FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    network-manager \
    gcc \
    make \
    libpcap-dev \
    tcpdump \
    nmap \
    iproute2 \
    iputils-ping \
    net-tools \
    curl \
    wget \
    dnsutils \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /CybICS

# Create directories first
RUN mkdir -p training pics data scripts

# Copy files (assuming root build context)
COPY software/landing/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY software/landing/app.py ./
COPY software/landing/ctf_config.json ./
COPY software/landing/pics/ pics/
COPY software/landing/templates/ templates/
COPY software/landing/static/ static/
COPY software/landing/utils/ utils/
COPY software/landing/modules/ modules/

# Copy training content from root
COPY training/ training/

# Copy attack scripts to /usr/local/bin for easy access
COPY training/flood_overwrite/flooding_hpt.py /usr/local/bin/flooding_hpt.py
RUN chmod +x /usr/local/bin/flooding_hpt.py

CMD [ "python", "./app.py" ]
