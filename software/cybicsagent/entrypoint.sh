#!/bin/bash

echo "=== CybICS AI Agent Starting ==="

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
sleep 5

# Pull the lightweight model if not already present
echo "Checking for model: ${OLLAMA_MODEL:-tinyllama}"
ollama pull ${OLLAMA_MODEL:-tinyllama}

# Start Flask application
echo "Starting Flask application..."
exec python app.py
