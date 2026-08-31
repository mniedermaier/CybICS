FROM python:3.12-alpine AS protobuf-builder

# grpcio-tools carries protoc and is only needed to generate the bindings, so it
# stays in this stage and never reaches the runtime image.
RUN pip install --no-cache-dir grpcio-tools

WORKDIR /build
# Reached through the parent build context; see build_image in software/build.sh.
COPY stm32/proto/cybics.proto ./
RUN python -m grpc_tools.protoc -I. --python_out=. cybics.proto

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
COPY hwio-raspberry/requirements.txt ./
# Install Python packages - RPi.GPIO and smbus-cffi need compilation
RUN pip install --no-cache-dir -r requirements.txt
COPY hwio-raspberry/hardwareIO.py ./
COPY --from=protobuf-builder /build/cybics_pb2.py ./

CMD [ "python", "./hardwareIO.py" ]
