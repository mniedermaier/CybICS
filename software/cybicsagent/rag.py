"""CybICS AI Agent - RAG knowledge base (ChromaDB + sentence-transformers)"""
import os
import re
import logging
import threading

import chromadb
from chromadb.utils import embedding_functions

from config import COLLECTION_NAME, CHUNK_MAX_CHARS, RAG_RESULTS

logger = logging.getLogger(__name__)

# Initialize ChromaDB
chroma_client = chromadb.Client()

# Global collection reference
collection = None
# Use RLock (reentrant) to allow nested lock acquisition within same thread
_init_lock = threading.RLock()

# Lazy initialization of embedding function (thread-safe via lock)
_sentence_transformer_ef = None


def _get_embedding_function():
    """Lazy initialize sentence transformer embedding function with thread safety."""
    global _sentence_transformer_ef
    if _sentence_transformer_ef is None:
        with _init_lock:
            if _sentence_transformer_ef is None:
                _sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
    return _sentence_transformer_ef


def initialize_knowledge_base():
    """Initialize the knowledge base with CybICS documentation. Thread-safe.
    
    Note: With gunicorn prefork, each worker process has its own memory space,
    so collection is initialized once per worker (not shared between workers).
    This is fine - each worker gets its own ChromaDB client and collection.
    The lock ensures thread-safety within a single worker process.
    """
    global collection

    # Double-checked locking pattern for thread-safe lazy initialization
    if collection is not None:
        return

    with _init_lock:
        if collection is not None:
            return

        logger.info("Creating fresh knowledge base from mounted volumes...")

        try:
            chroma_client.delete_collection(name=COLLECTION_NAME)
            logger.info("Deleted existing knowledge base")
        except Exception:
            pass

        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_function()
        )

        knowledge_base = _load_markdown_files('/knowledge')

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


def query_knowledge_base(question, n_results=None, max_distance=1.2):
    """Query the knowledge base for relevant context.

    Args:
        question: The query string.
        n_results: Number of results to return.
        max_distance: Maximum distance threshold. Results further than this
                      are considered irrelevant and filtered out.
    """
    if not collection:
        return []

    if n_results is None:
        n_results = RAG_RESULTS

    try:
        results = collection.query(
            query_texts=[question],
            n_results=n_results,
            include=['documents', 'distances']
        )

        if results and results['documents']:
            docs = results['documents'][0]
            distances = results['distances'][0] if results.get('distances') else []

            # Filter out low-relevance results
            if distances:
                filtered = [
                    _clean_context(doc) for doc, dist in zip(docs, distances)
                    if dist <= max_distance
                ]
                return filtered

            return [_clean_context(doc) for doc in docs]
        return []
    except Exception as e:
        logger.error(f"Error querying knowledge base: {e}")
        return []


def _clean_context(text):
    """Strip markdown links with file paths from RAG context.

    Converts [link text](some/path.md) to just 'link text' so the model
    doesn't copy broken file-path URLs into its responses.
    """
    # [text](path/to/file.md) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\.md[^)]*\)', r'\1', text)
    # [text](relative/path) → text  (no http/https)
    text = re.sub(r'\[([^\]]+)\]\((?!https?://)([^)]+)\)', r'\1', text)
    return text


def get_collection():
    """Get the current ChromaDB collection."""
    return collection


def _load_markdown_files(base_path='/knowledge'):
    """Scan and load all markdown files from knowledge directory."""
    knowledge = []
    doc_id = 0

    logger.info(f"Scanning for documentation in {base_path}...")

    file_count = 0
    training_modules = set()

    # Directories to skip (virtual envs, package managers, build artifacts)
    skip_dirs = {'.venv', 'venv', 'node_modules', 'site-packages', '__pycache__', '.git'}

    for root, dirs, files in os.walk(base_path):
        # Prune ignored directories in-place so os.walk won't descend into them
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for filename in files:
            if filename.endswith('.md') or filename.endswith('.MD'):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, base_path)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if not content.strip():
                        continue

                    path_parts = relative_path.split(os.sep)
                    doc_type = 'documentation'
                    topic = 'general'

                    if 'training' in path_parts:
                        doc_type = 'training'
                        if len(path_parts) > 1:
                            topic = path_parts[1]
                            training_modules.add(topic)
                    elif 'doc' in path_parts:
                        doc_type = 'documentation'
                    elif filename == 'README.md' and len(path_parts) == 1:
                        doc_type = 'core'
                        topic = 'overview'

                    chunks = _split_into_chunks(content)

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

                    logger.info(f"Loaded {len(chunks)} chunks from {relative_path}")
                    file_count += 1

                except Exception as e:
                    logger.error(f"Error loading {filepath}: {e}")
                    continue

    logger.info("=" * 60)
    logger.info(f"Knowledge Base Summary:")
    logger.info(f"  - Files processed: {file_count}")
    logger.info(f"  - Total chunks: {len(knowledge)}")
    logger.info(f"  - Training modules: {len(training_modules)}")
    if training_modules:
        logger.info(f"  - Modules: {', '.join(sorted(training_modules))}")
    logger.info("=" * 60)

    return knowledge


def _split_into_chunks(text, max_chars=None):
    """Split text into chunks by paragraphs, respecting max_chars limit."""
    if max_chars is None:
        max_chars = CHUNK_MAX_CHARS

    paragraphs = text.split('\n\n')

    chunks = []
    current_chunk = []
    current_length = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_length = len(para)

        if current_length + para_length > max_chars and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_length = para_length
        else:
            current_chunk.append(para)
            current_length += para_length + 2

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks if chunks else [text]
