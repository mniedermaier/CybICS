# CybICS AI Agent

An intelligent AI training coach for the CybICS ICS security training platform. Guides students through exercises with live system interaction, CTF progress tracking, and hands-on demonstrations.

## Features

- **Interactive Training Coach**: Step-by-step guidance through ICS security exercises with progressive hints
- **Live Process Monitoring**: Real-time tank pressures, compressor state, and blowout detection from HWIO
- **CTF Progress Tracking**: Shows solved challenges, points, and recommends next exercises
- **Defense Challenge Verification**: Auto-checks password hardening, firewall rules, network segmentation, IDS tuning
- **Network Traffic Analysis**: Captures and analyzes Modbus, S7comm, OPC-UA protocol traffic
- **IDS Forensics Assistant**: Alert summaries, forensics briefings, and investigation guidance
- **ICS Protocol Tools**: Read Modbus registers, browse OPC-UA nodes, check IDS alerts
- **Native Tool Calling**: Ollama function calling for capable models (llama3, phi3, mistral)
- **Keyword Fallback**: Reliable keyword dispatch for lightweight models (TinyLlama)
- **Streaming Responses**: Server-Sent Events (SSE) for token-by-token output
- **Conversation History**: Session-based multi-turn conversations
- **Local Execution**: Runs entirely within your infrastructure

## Architecture

```
cybicsagent/
├── app.py              # Flask app entry point
├── config.py           # Configuration & model capabilities
├── agent.py            # Dual-mode dispatch (native + keyword)
├── rag.py              # ChromaDB knowledge base
├── session.py          # Conversation session manager
├── routes.py           # Flask route handlers
└── tools/
    ├── __init__.py     # Tool registry & schema generator
    ├── containers.py   # Docker container management
    ├── system.py       # System stats & image listing
    ├── network.py      # nmap network scanning
    ├── ics.py          # Modbus, OPC-UA, IDS, process monitoring
    ├── training.py     # CTF progress, defense verification, packet analysis
    └── formatters.py   # Tool result formatting
```

**Stack**: Flask, ChromaDB, Ollama, sentence-transformers, pymodbus, asyncua

## Available Tools

### Container Management
| Tool | Description |
|------|-------------|
| `get_container_status` | List all running Docker containers |
| `restart_containers` | Restart one or all containers (requires confirmation) |
| `get_container_logs` | View recent logs from a container |

### System Monitoring
| Tool | Description |
|------|-------------|
| `get_system_stats` | CPU, memory, network stats for all containers |
| `list_docker_images` | List available Docker images |

### Network Operations
| Tool | Description |
|------|-------------|
| `execute_network_scan` | Run nmap scans (basic/port/service/vuln) |

### ICS Protocol Tools
| Tool | Description |
|------|-------------|
| `read_modbus_registers` | Read holding/input/coil/discrete registers from OpenPLC |
| `read_opcua_nodes` | Browse or read OPC-UA nodes from the OPC-UA server |
| `check_ids_alerts` | Check IDS status and recent intrusion alerts |
| `get_process_state` | Live physical process state (tank pressures, compressor, valves, sensors) |
| `get_ids_summary` | Alert summary with severity breakdown, top attackers, rule stats |
| `get_ids_forensics_briefing` | Forensics challenge briefing with investigation questions |

### Training & CTF Tools
| Tool | Description |
|------|-------------|
| `get_ctf_progress` | CTF progress: solved challenges, points, category breakdown |
| `verify_defense_challenge` | Auto-verify defense challenges (passwords, firewall, segmentation, IDS) |
| `get_network_packets` | Captured network packets with protocol analysis |
| `get_capture_stats` | Network capture statistics and protocol breakdown |

## How Tool Dispatch Works

The agent uses a **dual-mode** approach:

### Native Tool Calling (capable models)
When using models like `llama3.2:3b`, `phi3:mini`, or `mistral:7b`, the agent passes tool schemas directly to Ollama's API. The LLM decides when to call tools and what parameters to use.

### Keyword Fallback (small models)
When using `tinyllama` or other models without tool calling support, the agent detects intent from keywords in the user's question and dispatches tools automatically.

| User Says | Tool Triggered |
|-----------|---------------|
| "status", "running", "list containers" | `get_container_status` |
| "restart openplc" | `restart_containers` |
| "cpu", "memory", "stats" | `get_system_stats` |
| "logs from landing" | `get_container_logs` |
| "scan", "nmap" | `execute_network_scan` |
| "modbus", "register" | `read_modbus_registers` |
| "opcua", "opc-ua" | `read_opcua_nodes` |
| "ids", "alert", "intrusion" | `check_ids_alerts` |
| "pressure", "tank", "compressor", "blowout" | `get_process_state` |
| "progress", "score", "ctf", "what next" | `get_ctf_progress` |
| "verify", "check my" + defense keyword | `verify_defense_challenge` |
| "packet", "capture", "traffic", "wireshark" | `get_network_packets` |
| "forensic", "investigation", "incident" | `get_ids_forensics_briefing` |
| "ids summary", "top attacker" | `get_ids_summary` |

## Streaming

The agent supports Server-Sent Events (SSE) for streaming responses token-by-token:

- **Endpoint**: `POST /api/chat/stream`
- **Format**: `text/event-stream` with JSON events
- **Event types**: `session`, `tool`, `token`, `content`, `done`
- **Fallback**: The frontend automatically falls back to non-streaming on error

## Conversation History

Sessions are maintained in-memory with automatic cleanup:

- **Session ID**: Generated client-side (UUID), sent with each request
- **Max sessions**: 50 (oldest evicted automatically)
- **History limit**: 6 messages for TinyLlama, 20 for larger models
- **Multi-turn**: Supports contextual follow-ups ("restart the one that was failing")

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Send message (non-streaming) |
| `POST` | `/api/chat/stream` | Send message (SSE streaming) |
| `GET` | `/api/info` | Agent info & capabilities |
| `GET` | `/api/tools` | List available tools |
| `GET` | `/api/model` | Current model info |
| `POST` | `/api/model` | Change model |
| `POST` | `/api/model/pull` | Download a model |

### Chat Request
```json
{
  "message": "Show me the Modbus registers",
  "session_id": "optional-uuid"
}
```

### Chat Response
```json
{
  "response": "Here are the current Modbus holding registers...",
  "sources": 0,
  "tools_used": ["read_modbus_registers"],
  "tool_results": [...],
  "session_id": "uuid"
}
```

### Confirmation Response
```json
{
  "response": "This action requires confirmation: **Restart container: openplc**",
  "confirmation_required": true,
  "pending_action": {"tool": "restart_containers", "parameters": {"container_names": "openplc"}},
  "session_id": "uuid"
}
```

## Supported Models

| Model | Size | Quality | Tool Calling | Notes |
|-------|------|---------|-------------|-------|
| tinyllama | 600MB | 2/5 | Keyword only | Fast, low resource |
| phi3:mini | 2.3GB | 4/5 | Native | **Recommended** |
| llama3.2:3b | 2GB | 4/5 | Native | Great balance |
| mistral:7b | 4.1GB | 5/5 | Native | High quality |
| llama3.1:8b | 4.7GB | 5/5 | Native | Best quality |

Change models via the Settings UI or:
```bash
# Environment variable
OLLAMA_MODEL=phi3:mini

# API
curl -X POST http://localhost:5000/api/model -H 'Content-Type: application/json' -d '{"model": "phi3:mini"}'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `tinyllama` | Default LLM model |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OPENPLC_HOST` | `172.18.0.3` | OpenPLC Modbus host |
| `OPCUA_HOST` | `172.18.0.5` | OPC-UA server host |
| `IDS_HOST` | `172.18.0.1` | IDS server host (via gateway) |
| `IDS_PORT` | `8443` | IDS server port |
| `HWIO_HOST` | `172.18.0.2` | HWIO virtual simulation host |
| `HWIO_PORT` | `8090` | HWIO virtual simulation port |
| `LANDING_HOST` | `172.18.0.1` | Landing page host (for CTF/packet APIs) |
| `LANDING_PORT` | `80` | Landing page port |

## Knowledge Base

Dynamically loads documentation from mounted volumes at startup:

- `/knowledge/training/` - Training module READMEs
- `/knowledge/README.md` - Main CybICS README
- `/knowledge/doc/` - Additional documentation

Documents are split into 2000-character chunks and indexed with all-MiniLM-L6-v2 embeddings in ChromaDB.

## Adding New Tools

1. Create a function in the appropriate `tools/` module
2. Register it in `tools/__init__.py` `AVAILABLE_TOOLS` dict
3. Add a formatter in `tools/formatters.py`
4. Add keyword patterns in `agent.py` `detect_tool_intent()` (for small model fallback)
5. Rebuild the container

## Security Considerations

- Docker socket access required for container management
- Destructive actions (restart) require user confirmation
- ICS tools are read-only (no write operations)
- NET_ADMIN and NET_RAW capabilities required for nmap
- Only expose to trusted users on isolated networks
