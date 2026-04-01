#!/bin/bash
set -e

echo "=== CybICS AI Agent Starting ==="

MODEL="${OLLAMA_MODEL:-phi3:mini}"

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if ollama list >/dev/null 2>&1; then
        echo "Ollama is ready."
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: Ollama failed to start after 30 seconds"
        exit 1
    fi
    sleep 1
done

# Only pull if model is not already available
if ollama list | grep -q "$(echo "$MODEL" | cut -d: -f1)"; then
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
