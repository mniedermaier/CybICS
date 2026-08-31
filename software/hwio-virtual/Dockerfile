FROM python:3.12-alpine

# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    build-base \
    libffi-dev

WORKDIR /CybICS
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p pics
RUN mkdir -p static/js
COPY hardwareAbstraction.py ./
COPY pics/CybICS_logo.png pics/CybICS_logo.png
COPY pics/favicon.ico pics/favicon.ico
COPY pics/pcb.png pics/pcb.png
COPY static/js/*.js static/js/

CMD [ "python", "-u", "./hardwareAbstraction.py" ]
