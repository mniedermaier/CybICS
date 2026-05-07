#!/bin/bash

echo "=== CybICS AI Agent Starting ==="

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
  if ollama list >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

MODEL_NAME="${OLLAMA_MODEL:-tinyllama}"
FORCE_PULL="${FORCE_MODEL_PULL:-false}"

# Pull model only if missing (or explicitly forced)
echo "Checking for model: ${MODEL_NAME}"
if [ "${FORCE_PULL}" = "true" ] || [ "${FORCE_PULL}" = "1" ]; then
  echo "FORCE_MODEL_PULL is enabled. Pulling ${MODEL_NAME}..."
  ollama pull "${MODEL_NAME}"
elif ollama list | tail -n +2 | awk '{print $1}' | grep -Fxq "${MODEL_NAME}"; then
  echo "Model ${MODEL_NAME} already present. Skipping pull."
else
  echo "Model ${MODEL_NAME} not found locally. Pulling..."
  ollama pull "${MODEL_NAME}"
fi

# Start Flask application
echo "Starting Flask application..."
exec python app.py
