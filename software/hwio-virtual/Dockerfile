FROM python:3

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY hardwareAbstraction.py ./
COPY CybICS_logo.png ./
COPY favicon.ico ./

CMD [ "python", "./hardwareAbstraction.py" ]
