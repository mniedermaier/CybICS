#!/bin/bash
set -e

# Check if already configured (persistent volume)
if [ -f "/_appdata/.configured" ]; then
    echo "FUXA already configured, starting..."
    exec fuxa
fi

# Start FUXA in background for config import
fuxa &
FUXA_PID=$!

# Wait for FUXA API to be ready (up to 120 seconds for slow Pi)
echo "Waiting for FUXA to start..."
COUNTER=0
while ! curl -s http://localhost:1881/api/project 2>/dev/null | grep -q "devices"; do
    sleep 2
    COUNTER=$((COUNTER + 1))
    if [ $COUNTER -gt 60 ]; then
        echo "Timeout waiting for FUXA to start"
        exit 1
    fi
    echo "Waiting... ($((COUNTER * 2))s)"
done

echo "FUXA is ready, importing configuration..."

# Import configuration
curl -sf -X POST -H "Content-Type: application/json" -d @/config/fuxa-project.json http://localhost:1881/api/project && echo "Project imported"
curl -sf -X POST -H "Content-Type: application/json" -d @/config/add-user-viewer.json http://localhost:1881/api/users && echo "Viewer user added"
curl -sf -X POST -H "Content-Type: application/json" -d @/config/add-user-operator.json http://localhost:1881/api/users && echo "Operator user added"
curl -sf -X POST -H "Content-Type: application/json" -d @/config/settings.json http://localhost:1881/api/settings && echo "Settings applied"

# Mark as configured
touch /_appdata/.configured

echo "Configuration complete!"

# Keep FUXA running
wait $FUXA_PID
