FROM python:3.12-alpine AS protobuf-builder

# Install grpcio-tools for protobuf generation
RUN pip install --no-cache-dir grpcio-tools

WORKDIR /build
# Proto file is copied from stm32/proto/ via build context
COPY stm32/proto/cybics.proto ./
RUN python -m grpc_tools.protoc -I. --python_out=. cybics.proto

FROM python:3.12-alpine

RUN apk add --no-cache \
    networkmanager \
    networkmanager-cli \
    build-base \
    linux-headers \
    libffi-dev

WORKDIR /CybICS
COPY hwio-raspberry/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY hwio-raspberry/hardwareIO.py ./
COPY --from=protobuf-builder /build/cybics_pb2.py ./

CMD [ "python", "./hardwareIO.py" ]
