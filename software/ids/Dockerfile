FROM python:3.12-alpine AS builder

RUN apk add --no-cache \
    libpcap-dev \
    libffi-dev \
    build-base \
    linux-headers

WORKDIR /ids
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine

RUN apk add --no-cache \
    libpcap-dev \
    libffi \
    tcpdump \
    iproute2

COPY --from=builder /install /usr/local

# Fix: ctypes.util.find_library('pcap') fails on Alpine/musl.
# Patch Scapy's winpcapy.py to fall back to loading libpcap.so directly.
RUN sed -i 's|_lib_name = find_library("pcap")|_lib_name = find_library("pcap") or "libpcap.so"|' \
    /usr/local/lib/python3.12/site-packages/scapy/libs/winpcapy.py

WORKDIR /ids
COPY . .

EXPOSE 8443

CMD ["python", "ids_server.py"]
