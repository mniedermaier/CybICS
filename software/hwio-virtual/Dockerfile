FROM python:3-slim

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p pics
COPY hardwareAbstraction.py ./
COPY pics/CybICS_logo.png pics/CybICS_logo.png
COPY pics/favicon.ico pics/favicon.ico
COPY pics/pcb.png pics/pcb.png

CMD [ "python", "./hardwareAbstraction.py" ]
