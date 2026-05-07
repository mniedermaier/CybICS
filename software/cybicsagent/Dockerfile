# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/opt/model-cache/huggingface \
    TRANSFORMERS_CACHE=/opt/model-cache \
    SENTENCE_TRANSFORMERS_HOME=/opt/model-cache

# Install system dependencies including Ollama, Docker CLI, and nmap
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    nmap \
    zstd \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && chmod a+r /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bullseye stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli

# Install Ollama once in a stable base layer
RUN curl -fsSL https://ollama.com/install.sh | sh

FROM base AS python-deps

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
WORKDIR /tmp/build

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Download sentence transformer model at build time and keep it in a dedicated cache dir
RUN mkdir -p /opt/model-cache \
    && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2', cache_folder='/opt/model-cache')"

FROM base AS runtime

ENV PATH="/opt/venv/bin:${PATH}"
WORKDIR /app

COPY --from=python-deps /opt/venv /opt/venv
COPY --from=python-deps /opt/model-cache /opt/model-cache
COPY app.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# 5000 for Flask app, 11434 for Ollama
EXPOSE 5000 11434

CMD ["./entrypoint.sh"]
