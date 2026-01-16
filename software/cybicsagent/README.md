# CybICS AI Agent

An intelligent AI assistant for the CybICS platform with system control capabilities, providing both information and hands-on support.

## Features

- **Lightweight LLM**: Uses TinyLlama (600MB) for fast, efficient responses
- **RAG-based**: Retrieval Augmented Generation with CybICS knowledge base
- **Function Calling**: Can execute system operations and control CybICS infrastructure
- **Container Management**: Restart, monitor, and manage Docker containers
- **System Monitoring**: Real-time stats and resource usage
- **Network Analysis**: Built-in nmap scanning capabilities
- **Local Execution**: Runs entirely within your infrastructure
- **Context-Aware**: Understands CybICS components, training modules, and troubleshooting

## Architecture

- **Frontend**: Chat widget integrated into landing page
- **Backend**: Flask API with ChromaDB vector database
- **LLM**: Ollama with TinyLlama model
- **Embeddings**: all-MiniLM-L6-v2 for semantic search

## Available Tools

The agent can execute the following system operations:

### Container Management
- **`get_container_status`**: Get status of all running Docker containers
- **`restart_containers`**: Restart one or all containers
- **`get_container_logs`**: View recent logs from a specific container

### System Monitoring
- **`get_system_stats`**: Real-time CPU, memory, and network stats for all containers

### Network Operations
- **`execute_network_scan`**: Run nmap scans (basic/port/service/vuln)

### Docker Management
- **`list_docker_images`**: List all available Docker images

## How It Works

The agent uses **intelligent keyword detection** to automatically trigger tools, making it reliable even with smaller models:

### Automatic Tool Detection

The agent detects intent from natural language questions:

| User Says | Tool Triggered | Example |
|-----------|----------------|---------|
| "status", "running", "list containers" | `get_container_status` | "Show me container status" |
| "restart [container]" | `restart_containers` | "Restart the OpenPLC container" |
| "cpu", "memory", "stats", "performance" | `get_system_stats` | "What's the CPU usage?" |
| "logs [container]" | `get_container_logs` | "Show logs from landing" |
| "scan", "nmap", "network" | `execute_network_scan` | "Scan the network" |
| "image", "docker image" | `list_docker_images` | "List Docker images" |

### Example Conversations

**Question:** "Can you show me the status of all containers?"
- ✅ Detects keywords: "status", "containers"
- ✅ Executes: `get_container_status`
- ✅ Returns formatted table with container info

**Question:** "Restart the OpenPLC container"
- ✅ Detects keywords: "restart", "openplc"
- ✅ Executes: `restart_containers(container_names="openplc")`
- ✅ Confirms restart was successful

**Question:** "Show me the last 100 lines of logs from the landing container"
- ✅ Detects keywords: "logs", "landing", "100"
- ✅ Executes: `get_container_logs(container_name="landing", lines=100)`
- ✅ Returns formatted log output

**Question:** "Scan the CybICS network for devices"
- ✅ Detects keywords: "scan", "network"
- ✅ Executes: `execute_network_scan(target="172.18.0.0/24", scan_type="basic")`
- ✅ Returns scan results

This approach ensures reliable tool execution regardless of model size!

## API Endpoints

### `GET /health`
Health check endpoint

### `POST /api/chat`
Send a message to the agent (now with tool calling support)
```json
{
  "message": "Restart all containers"
}
```

Response (with tools):
```json
{
  "response": "I've successfully restarted all 6 containers...",
  "sources": 0,
  "tools_used": ["restart_containers"],
  "tool_results": [...]
}
```

Response (without tools):
```json
{
  "response": "You can access the OpenPLC interface...",
  "sources": 2
}
```

### `GET /api/info`
Get agent information and status (includes capabilities and tool count)

### `GET /api/tools`
List all available tools with descriptions and parameters

## Environment Variables

- `OLLAMA_MODEL`: Model to use (default: tinyllama)
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)

## Supported Models

The agent works with various Ollama models. Larger models provide better responses:

- **`tinyllama`** (600MB) - Ultra-lightweight, fast responses, basic capability
- **`phi3:mini`** (2.3GB) - **Recommended** - Good balance of size and quality
- **`llama3.2:3b`** (2GB) - Excellent quality, still lightweight
- **`mistral:7b`** (4.1GB) - High quality responses, requires more resources
- **`llama3.1:8b`** (4.7GB) - Best quality, most resource intensive

To change the model, you can:

**Option 1: Via Settings UI (Recommended)**
1. Open CybICS landing page
2. Click Settings (⚙️)
3. Go to AI Assistant section
4. Select model from dropdown
5. Wait for download to complete (if needed)

**Option 2: Via Environment Variable**
Set `OLLAMA_MODEL` in docker-compose.yml:

```yaml
environment:
  - OLLAMA_MODEL=phi3:mini  # Change this line
```

**Download Times**: First-time model downloads can take:
- **tinyllama** (600MB): ~2-5 minutes
- **phi3:mini** (2.3GB): ~5-15 minutes
- **llama3.2:3b** (2GB): ~5-15 minutes
- **mistral:7b** (4.1GB): ~10-30 minutes
- **llama3.1:8b** (4.7GB): ~10-30 minutes

Times vary based on your internet connection speed. The system will wait up to 30 minutes for downloads to complete.

### Model Comparison

| Model | Size | Quality | Speed | Tool Calling |
|-------|------|---------|-------|--------------|
| tinyllama | 600MB | ⭐⭐ | ⚡⚡⚡ | Basic |
| phi3:mini | 2.3GB | ⭐⭐⭐⭐ | ⚡⚡ | Good |
| llama3.2:3b | 2GB | ⭐⭐⭐⭐ | ⚡⚡ | Excellent |
| mistral:7b | 4.1GB | ⭐⭐⭐⭐⭐ | ⚡ | Excellent |

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

### Adding New Knowledge
1. Add or modify markdown files in `training/`, `doc/`, or root README
2. Restart the cybicsagent container: `docker compose restart cybicsagent`
3. Knowledge base will be rebuilt automatically with new content

No code changes needed - the agent scans all mounted documentation!

### Adding New Tools
To add new capabilities:
1. Add a function in `app.py` (see existing tools as examples)
2. Register it in `AVAILABLE_TOOLS` dictionary with description and parameters
3. Rebuild the container

Example tool:
```python
def my_new_tool(param1, param2="default"):
    """Tool description"""
    try:
        # Your implementation
        return {'success': True, 'result': 'data'}
    except Exception as e:
        return {'error': str(e)}

# Register in AVAILABLE_TOOLS
AVAILABLE_TOOLS['my_new_tool'] = {
    'function': my_new_tool,
    'description': 'What this tool does',
    'parameters': {
        'param1': {'type': 'string', 'description': 'First param', 'required': True},
        'param2': {'type': 'string', 'description': 'Optional param', 'optional': True}
    }
}
```

### Testing Locally
```bash
docker build -t cybicsagent .
docker run -p 5000:5000 -p 11434:11434 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cybicsagent
```

**Note**: The Docker socket mount is required for container management tools to work.

## Performance

- Initial model load: ~30 seconds
- Response time (Q&A): 2-5 seconds depending on question complexity
- Response time (with tools): 5-15 seconds depending on tool execution
- Memory usage: ~1.5GB RAM
- CPU: Works on CPU-only systems (GPU optional)

## Security Considerations

The agent has access to Docker socket and can execute system operations. Ensure:
- Only trusted users have access to the agent
- Network isolation is properly configured
- The agent is not exposed to untrusted networks
- Container capabilities (NET_ADMIN, NET_RAW) are required for network scanning

## Version History

### v2.1.0 (Current)
- **Intelligent keyword-based tool detection** - works reliably with any model size
- Simplified prompts for better compatibility with small models
- Improved markdown formatting in responses
- Better tool result formatting
- Enhanced error messages
- Model size recommendations and comparison table

### v2.0.0
- Added function calling capabilities
- Container management tools (status, restart, logs)
- System monitoring and stats
- Network scanning with nmap
- Docker image management
- Enhanced tool execution framework

### v1.0.0
- Initial release with RAG-based Q&A
- Dynamic knowledge base loading
- Basic chat functionality
