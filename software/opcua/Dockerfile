FROM python:3.12-alpine

# iptables lets the network-segmentation defense challenge add a rule that
# blocks the attack machine from the OPC-UA port (needs NET_ADMIN, granted in
# the compose files).
RUN apk add --no-cache iptables

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ADD certificates ./certificates
COPY opcua.py ./
COPY opcua.py ./ \
    user_manager.py ./

CMD [ "python", "./opcua.py" ]
