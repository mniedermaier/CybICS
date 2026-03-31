"""
CybICS AI Agent - Intelligent assistant for the CybICS ICS training platform.

Features:
- Native Ollama tool calling (llama3, phi3, mistral, etc.)
- Keyword-based tool fallback (TinyLlama and other small models)
- RAG knowledge base (ChromaDB + sentence-transformers)
- Conversation history with session management
- Streaming responses via SSE
- ICS-specific tools (Modbus, OPC-UA, IDS)
- Destructive action confirmation
"""
import logging

from flask import Flask
from flask_cors import CORS

import config
from rag import initialize_knowledge_base
from routes import register_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CybICS Agent - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Register all route handlers
register_routes(app)

if __name__ == '__main__':
    logger.info("Starting CybICS AI Agent v3.0.0...")
    logger.info(f"Using Ollama model: {config.OLLAMA_MODEL}")
    logger.info(f"Ollama host: {config.OLLAMA_HOST}")
    logger.info(f"Native tool calling: {config.model_supports_tools(config.OLLAMA_MODEL)}")

    # Initialize knowledge base
    initialize_knowledge_base()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
