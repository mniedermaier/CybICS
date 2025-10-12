FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir flask psutil

COPY host-stats.py .

CMD ["python", "host-stats.py"]
