FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    libffi-dev \
    build-base

WORKDIR /ids
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine

RUN apk add --no-cache \
    libffi \
    tcpdump \
    iproute2

COPY --from=builder /install /usr/local

WORKDIR /ids
COPY . .

EXPOSE 8443

CMD ["python", "ids_server.py"]
