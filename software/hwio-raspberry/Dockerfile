FROM python:3.12-alpine

RUN apk add --no-cache \
    networkmanager \
    networkmanager-cli \
    build-base \
    python3-dev \
    libffi-dev \
    i2c-tools \
    py3-pip

WORKDIR /CybICS
COPY requirements.txt ./
# Install Python packages - RPi.GPIO and smbus-cffi need compilation
RUN pip install --no-cache-dir -r requirements.txt
COPY hardwareIO.py ./

CMD [ "python", "./hardwareIO.py" ]
