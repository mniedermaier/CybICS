FROM python:3

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ADD certificates ./certificates
COPY opcua.py ./
COPY opcua.py ./ \
    user_manager.py ./

CMD [ "python", "./opcua.py" ]
