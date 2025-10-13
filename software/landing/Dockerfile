FROM python:3.10.15-slim

RUN apt-get update && apt-get install -y \
    network-manager \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /CybICS

# Create directories first
RUN mkdir -p training pics data

# Copy files (assuming root build context)
COPY software/landing/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY software/landing/app.py ./
COPY software/landing/ctf_config.json ./
COPY software/landing/pics/ pics/
COPY software/landing/templates/ templates/
COPY software/landing/static/ static/

# Copy training content from root
COPY training/ training/

CMD [ "python", "./app.py" ]
