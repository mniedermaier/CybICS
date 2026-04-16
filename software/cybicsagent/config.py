"""CybICS AI Agent - Configuration"""
import os
import threading

# Ollama settings
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'phi3:mini')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

# Knowledge base
COLLECTION_NAME = "cybics_knowledge"
CHUNK_MAX_CHARS = 2000
RAG_RESULTS = 3

# Thread-local storage for mutable state
_local = threading.local()

# Default model (immutable)
DEFAULT_MODEL = OLLAMA_MODEL

# Known CybICS container names (for keyword-based tool dispatch)
CYBICS_CONTAINERS = [
    'openplc', 'fuxa', 'hwio', 'opcua', 's7com',
    'landing', 'cybicsagent', 'engineeringws', 'attack',
    'ids', 'stm32',
]

# CybICS network addresses
OPENPLC_HOST = os.getenv('OPENPLC_HOST', '172.18.0.3')
OPCUA_HOST = os.getenv('OPCUA_HOST', '172.18.0.5')
IDS_HOST = os.getenv('IDS_HOST', '172.18.0.1')
IDS_PORT = int(os.getenv('IDS_PORT', '8443'))
MODBUS_PORT = 502
OPCUA_PORT = 4840
HWIO_HOST = os.getenv('HWIO_HOST', '172.18.0.2')
HWIO_PORT = int(os.getenv('HWIO_PORT', '8090'))
LANDING_HOST = os.getenv('LANDING_HOST', '172.18.0.1')
LANDING_PORT = int(os.getenv('LANDING_PORT', '80'))

# Models known to support native tool/function calling
TOOL_CAPABLE_MODELS = [
    'llama3', 'llama3.1', 'llama3.2', 'llama3.3',
    'mistral', 'mixtral',
    'phi3', 'phi4',
    'qwen', 'qwen2', 'qwen2.5', 'qwen3',
    'command-r',
    'nemotron',
    'granite3',
    'deepseek-r1',
]

# Session limits
MAX_SESSIONS = 50
MAX_HISTORY_LARGE_MODEL = 20
MAX_HISTORY_SMALL_MODEL = 6

# Models considered "small" (limited context window)
SMALL_MODELS = []


def current_model() -> str:
    """Get the current model for this thread. Thread-safe."""
    if not hasattr(_local, 'model'):
        _local.model = DEFAULT_MODEL
    return _local.model


def set_current_model(model: str):
    """Set the current model for this thread. Thread-safe."""
    _local.model = model


def model_supports_tools(model_name: str = None) -> bool:
    """Check if a model supports native Ollama tool calling."""
    if model_name is None:
        model_name = current_model()
    name = model_name.lower().split(':')[0]
    return any(name.startswith(prefix) for prefix in TOOL_CAPABLE_MODELS)


def get_max_history(model_name: str = None) -> int:
    """Get max conversation history length for a model."""
    if model_name is None:
        model_name = current_model()
    name = model_name.lower().split(':')[0]
    if any(name.startswith(s) for s in SMALL_MODELS):
        return MAX_HISTORY_SMALL_MODEL
    return MAX_HISTORY_LARGE_MODEL
