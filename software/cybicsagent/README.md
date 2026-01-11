# CybICS AI Agent

A lightweight AI assistant for the CybICS platform, providing intelligent help and support for users.

## Features

- **Lightweight LLM**: Uses TinyLlama (600MB) for fast, efficient responses
- **RAG-based**: Retrieval Augmented Generation with CybICS knowledge base
- **Local Execution**: Runs entirely within your infrastructure
- **Context-Aware**: Understands CybICS components, training modules, and troubleshooting

## Architecture

- **Frontend**: Chat widget integrated into landing page
- **Backend**: Flask API with ChromaDB vector database
- **LLM**: Ollama with TinyLlama model
- **Embeddings**: all-MiniLM-L6-v2 for semantic search

## API Endpoints

### `GET /health`
Health check endpoint

### `POST /api/chat`
Send a message to the agent
```json
{
  "message": "How do I access the OpenPLC interface?"
}
```

Response:
```json
{
  "response": "You can access the OpenPLC interface...",
  "sources": 2
}
```

### `GET /api/info`
Get agent information and status

## Environment Variables

- `OLLAMA_MODEL`: Model to use (default: tinyllama)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)

## Supported Models

- `tinyllama`: Ultra-lightweight (600MB), fast responses
- `phi`: Microsoft's Phi-2 (1.7GB), better quality
- `llama3.2:1b`: Meta's smallest Llama 3.2 (1.3GB)

To change the model, set `OLLAMA_MODEL` environment variable in docker-compose.yml

## Knowledge Base

The agent dynamically loads documentation from mounted volumes at startup:

**Sources:**
- `/knowledge/training/` - All training module READMEs (dynamically loaded)
- `/knowledge/README.md` - Main CybICS README
- `/knowledge/doc/` - Additional documentation

**What it knows:**
- CybICS architecture and components
- Services and ports
- All training modules with detailed instructions
- CTF challenges and solutions
- Common troubleshooting steps
- Security testing procedures
- Protocol details (Modbus, OPC UA, S7)

**Dynamic Loading:**
- Knowledge base is rebuilt fresh every time the container starts
- No static embedded content - always uses latest documentation
- Automatically discovers all `.md` files in mounted volumes
- Splits large documents into 2000-character chunks for better retrieval
- Preserves source file paths and metadata

## Usage

The agent appears as a chat widget in the bottom-left corner of the landing page.
Click to expand and ask questions about CybICS.

Can be enabled/disabled via Settings panel.

## Development

To add new knowledge:
1. Add or modify markdown files in `training/`, `doc/`, or root README
2. Restart the cybicsagent container: `docker compose restart cybicsagent`
3. Knowledge base will be rebuilt automatically with new content

No code changes needed - the agent scans all mounted documentation!

To test locally:
```bash
docker build -t cybicsagent .
docker run -p 5000:5000 -p 11434:11434 cybicsagent
```

## Performance

- Initial model load: ~30 seconds
- Response time: 2-5 seconds depending on question complexity
- Memory usage: ~1.5GB RAM
- CPU: Works on CPU-only systems (GPU optional)
