FROM python:3.12-alpine

RUN apk add --no-cache \
    networkmanager \
    networkmanager-cli \
    build-base \
    linux-headers \
    libffi-dev

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY hardwareIO.py ./

CMD [ "python", "./hardwareIO.py" ]
