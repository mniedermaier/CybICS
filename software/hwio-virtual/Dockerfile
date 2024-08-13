FROM python:3

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY hardwareAbstraction.py ./
COPY CybICS_logo.png ./

CMD [ "python", "./hardwareAbstraction.py" ]
