FROM python:3.11-slim

# Install system dependencies including Ollama
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download sentence transformer model at build time
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY app.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Expose ports
# 5000 for Flask app
# 11434 for Ollama
EXPOSE 5000 11434

# Use entrypoint script to start both Ollama and Flask
CMD ["./entrypoint.sh"]
