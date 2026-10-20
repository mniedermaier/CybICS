FROM python:3.12-alpine

# iptables lets the network-segmentation defense challenge add a rule that
# blocks the attack machine from the OPC-UA port (needs NET_ADMIN, granted in
# the compose files).
RUN apk add --no-cache iptables

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Pre-build the standard address space as a shelf (see opcua.py). It is built
# here, under the target platform, because the dbm file format is the
# interpreter's own.
RUN python -c "import asyncio; from pathlib import Path; from asyncua import Server; asyncio.run(Server().init(Path('address_space.shelf')))" \
    && test -f address_space.shelf
ADD certificates ./certificates
COPY opcua.py ./
COPY opcua.py ./ \
    user_manager.py ./

CMD [ "python", "./opcua.py" ]
