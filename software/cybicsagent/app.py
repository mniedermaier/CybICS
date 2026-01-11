"""
CybICS AI Agent - A lightweight LLM assistant for CybICS platform
"""
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import chromadb
from chromadb.utils import embedding_functions
import ollama

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CybICS Agent - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'tinyllama')
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
COLLECTION_NAME = "cybics_knowledge"

# Initialize ChromaDB
chroma_client = chromadb.Client()
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Global collection reference
collection = None


def initialize_knowledge_base():
    """Initialize the knowledge base with CybICS documentation"""
    global collection

    # Always recreate collection to get fresh documentation
    logger.info("Creating fresh knowledge base from mounted volumes...")

    # Delete existing collection if it exists
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
        logger.info("Deleted existing knowledge base")
    except Exception:
        pass

    # Create new collection
    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=sentence_transformer_ef
    )

    # Load documentation from mounted volumes
    knowledge_base = load_markdown_files('/knowledge')

    if knowledge_base:
        logger.info(f"Adding {len(knowledge_base)} documents to vector database...")
        collection.add(
            documents=[doc['content'] for doc in knowledge_base],
            ids=[doc['id'] for doc in knowledge_base],
            metadatas=[doc['metadata'] for doc in knowledge_base]
        )
        logger.info(f"Knowledge base initialized with {len(knowledge_base)} document chunks")
    else:
        logger.warning("No knowledge base documents found - check if volumes are mounted correctly")


def load_markdown_files(base_path='/knowledge'):
    """Scan and load all markdown files from knowledge directory"""
    import os
    import re

    knowledge = []
    doc_id = 0

    logger.info(f"Scanning for documentation in {base_path}...")

    # Track statistics
    file_count = 0
    training_modules = set()

    # Walk through all directories
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if filename.endswith('.md') or filename.endswith('.MD'):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, base_path)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Skip empty files
                    if not content.strip():
                        continue

                    # Extract metadata from path
                    path_parts = relative_path.split(os.sep)
                    doc_type = 'documentation'
                    topic = 'general'

                    if 'training' in path_parts:
                        doc_type = 'training'
                        # Get the training module name (parent directory)
                        if len(path_parts) > 1:
                            topic = path_parts[1]
                            training_modules.add(topic)
                    elif 'doc' in path_parts:
                        doc_type = 'documentation'
                    elif filename == 'README.md' and len(path_parts) == 1:
                        doc_type = 'core'
                        topic = 'overview'

                    # Split large documents into chunks (max 2000 chars per chunk)
                    chunks = split_into_chunks(content, max_chars=2000)

                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            doc_id += 1
                            knowledge.append({
                                'id': f'doc_{doc_id:04d}',
                                'content': chunk,
                                'metadata': {
                                    'type': doc_type,
                                    'topic': topic,
                                    'source': relative_path,
                                    'chunk': i,
                                    'total_chunks': len(chunks)
                                }
                            })

                    logger.info(f"✓ Loaded {len(chunks)} chunks from {relative_path}")
                    file_count += 1

                except Exception as e:
                    logger.error(f"Error loading {filepath}: {e}")
                    continue

    # Log summary
    logger.info("="*60)
    logger.info(f"Knowledge Base Summary:")
    logger.info(f"  - Files processed: {file_count}")
    logger.info(f"  - Total chunks: {len(knowledge)}")
    logger.info(f"  - Training modules: {len(training_modules)}")
    if training_modules:
        logger.info(f"  - Modules: {', '.join(sorted(training_modules))}")
    logger.info("="*60)

    return knowledge


def split_into_chunks(text, max_chars=2000):
    """Split text into chunks by paragraphs, respecting max_chars limit"""
    # Split by double newlines (paragraphs)
    paragraphs = text.split('\n\n')

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_length = len(para)

        # If adding this paragraph exceeds limit, save current chunk
        if current_length + para_length > max_chars and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_length = para_length
        else:
            current_chunk.append(para)
            current_length += para_length + 2  # +2 for \n\n

    # Add remaining chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks if chunks else [text]  # Fallback to original text if no chunks


def query_knowledge_base(question, n_results=3):
    """Query the knowledge base for relevant context"""
    if not collection:
        return []

    try:
        results = collection.query(
            query_texts=[question],
            n_results=n_results
        )

        if results and results['documents']:
            return results['documents'][0]
        return []
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return []


def generate_response(question, context):
    """Generate response using Ollama"""
    try:
        # Build prompt with context
        context_str = "\n\n".join(context) if context else "No specific context available."

        prompt = f"""You are the CybICS AI Assistant, an expert on the CybICS (Cyber-physical Industrial Control Systems) platform.
Answer the user's question based on the provided context. Be helpful, concise, and accurate.

Context:
{context_str}

User Question: {question}

Answer (be specific and helpful):"""

        # Call Ollama
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are the CybICS AI Assistant. Provide helpful, accurate answers about the CybICS platform.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )

        return response['message']['content']

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"I'm having trouble connecting to the AI model. Error: {str(e)}"


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': OLLAMA_MODEL,
        'knowledge_base_docs': collection.count() if collection else 0
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    try:
        data = request.get_json()
        question = data.get('message', '').strip()

        if not question:
            return jsonify({'error': 'No message provided'}), 400

        logger.info(f"Received question: {question}")

        # Query knowledge base
        context = query_knowledge_base(question)

        # Generate response
        response = generate_response(question, context)

        return jsonify({
            'response': response,
            'sources': len(context)
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/info', methods=['GET'])
def info():
    """Get agent information"""
    try:
        # Try to get available models
        models = []
        try:
            models_response = ollama.list()
            models = [m['name'] for m in models_response.get('models', [])]
        except Exception:
            pass

        return jsonify({
            'name': 'CybICS AI Agent',
            'version': '1.0.0',
            'model': OLLAMA_MODEL,
            'available_models': models,
            'knowledge_base_docs': collection.count() if collection else 0,
            'status': 'ready'
        })
    except Exception as e:
        logger.error(f"Error in info endpoint: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting CybICS AI Agent...")
    logger.info(f"Using Ollama model: {OLLAMA_MODEL}")
    logger.info(f"Ollama host: {OLLAMA_HOST}")

    # Initialize knowledge base
    initialize_knowledge_base()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
