FROM python:3

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY readI2Cpi.py ./

CMD [ "python", "./readI2Cpi.py" ]
