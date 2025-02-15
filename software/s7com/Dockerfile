FROM python:3-slim

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY s7com.py ./

CMD [ "python", "./s7com.py" ]
