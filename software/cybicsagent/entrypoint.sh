#!/bin/bash
set -e

echo "=== CybICS AI Agent Starting ==="

MODEL="${OLLAMA_MODEL:-phi3:mini}"
MODEL_BASENAME="$(echo "$MODEL" | cut -d: -f1)"

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready with retry
MAX_RETRIES=30
RETRY_DELAY=1
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 $MAX_RETRIES); do
    # First check if Ollama process is responding
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    # Fallback: check if ollama CLI is working
    if ollama list >/dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    if [ "$i" -eq $MAX_RETRIES ]; then
        echo "ERROR: Ollama failed to start after $MAX_RETRIES seconds"
        exit 1
    fi
    sleep $RETRY_DELAY
done

# Only pull if model is not already available (exact match on model base name)
if ollama list | grep -qw "$MODEL_BASENAME"; then
    echo "Model $MODEL already available, skipping pull."
else
    echo "Pulling model: $MODEL"
    ollama pull "$MODEL" || { echo "ERROR: Failed to pull model $MODEL"; exit 1; }
fi

# Start with gunicorn (production WSGI server)
echo "Starting gunicorn..."
exec gunicorn app:app \
    --bind 0.0.0.0:5000 \
    --workers 2 \
    --threads 4 \
    --timeout 300 \
    --keep-alive 65 \
    --access-logfile - \
    --error-logfile -
