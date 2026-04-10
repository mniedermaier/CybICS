FROM python:3.12-slim

WORKDIR /opt/cybics/update-server

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 6689

CMD ["uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "6689"]
