FROM python:3

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY opcua.py ./

CMD [ "python", "./opcua.py" ]
