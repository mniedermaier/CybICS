"""
CybICS AI Agent - A lightweight LLM assistant for CybICS platform
Enhanced with function calling capabilities for system control
"""
import os
import logging
import json
import subprocess
import re
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

# Global variable to track current model (can be changed at runtime)
current_model = OLLAMA_MODEL

# Initialize ChromaDB
chroma_client = chromadb.Client()
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Global collection reference
collection = None


# ========== TOOL FUNCTIONS ==========

def get_container_status():
    """Get status of all CybICS Docker containers"""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {'error': f'Failed to get container status: {result.stderr}'}

        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return {
            'success': True,
            'total_containers': len(containers),
            'containers': containers
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        return {'error': str(e)}


def restart_containers(container_names=None):
    """
    Restart CybICS Docker containers
    Args:
        container_names: List of container names to restart, or None to restart all
    """
    try:
        # Get list of containers to restart
        if container_names:
            containers = container_names if isinstance(container_names, list) else [container_names]
        else:
            # Get all running containers
            ps_result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if ps_result.returncode != 0:
                return {'error': f'Failed to list containers: {ps_result.stderr}'}
            containers = [c for c in ps_result.stdout.strip().split('\n') if c]

        if not containers:
            return {'error': 'No containers found to restart'}

        # Restart each container
        failed = []
        succeeded = []
        for container in containers:
            result = subprocess.run(
                ['docker', 'restart', container],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                succeeded.append(container)
            else:
                failed.append(container)

        return {
            'success': len(failed) == 0,
            'restarted': succeeded,
            'failed': failed,
            'message': f'Restarted {len(succeeded)} container(s)'
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Restart operation timed out'}
    except Exception as e:
        return {'error': str(e)}


def get_container_logs(container_name, lines=50):
    """
    Get logs from a specific container
    Args:
        container_name: Name of the container
        lines: Number of lines to retrieve (default: 50)
    """
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', str(lines), '--timestamps', container_name],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return {'error': f'Failed to get logs: {result.stderr}'}

        return {
            'success': True,
            'container': container_name,
            'logs': result.stdout
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        return {'error': str(e)}


def get_system_stats():
    """Get system resource statistics"""
    try:
        # Get Docker stats
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {'error': f'Failed to get stats: {result.stderr}'}

        stats = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    stats.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return {
            'success': True,
            'container_stats': stats
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        return {'error': str(e)}


def execute_network_scan(target, scan_type='basic'):
    """
    Execute a network scan using nmap
    Args:
        target: Target IP or network (e.g., '10.0.0.0/24')
        scan_type: Type of scan - 'basic', 'port', 'service', 'vuln'
    """
    try:
        # Build nmap command based on scan type
        if scan_type == 'basic':
            cmd = ['nmap', '-sn', target]
        elif scan_type == 'port':
            cmd = ['nmap', '-p-', target]
        elif scan_type == 'service':
            cmd = ['nmap', '-sV', target]
        elif scan_type == 'vuln':
            cmd = ['nmap', '--script', 'vuln', target]
        else:
            return {'error': f'Unknown scan type: {scan_type}'}

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes for network scans
        )

        return {
            'success': True,
            'scan_type': scan_type,
            'target': target,
            'results': result.stdout
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Scan timed out (exceeded 5 minutes)'}
    except FileNotFoundError:
        return {'error': 'nmap not found - network scanning not available'}
    except Exception as e:
        return {'error': str(e)}


def list_docker_images():
    """List all Docker images on the system"""
    try:
        result = subprocess.run(
            ['docker', 'images', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return {'error': f'Failed to list images: {result.stderr}'}

        images = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    images.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        return {
            'success': True,
            'total_images': len(images),
            'images': images
        }
    except subprocess.TimeoutExpired:
        return {'error': 'Command timed out'}
    except Exception as e:
        return {'error': str(e)}


# Tool definitions for the LLM
AVAILABLE_TOOLS = {
    'get_container_status': {
        'function': get_container_status,
        'description': 'Get the status of all running Docker containers in CybICS',
        'parameters': {}
    },
    'restart_containers': {
        'function': restart_containers,
        'description': 'Restart one or more Docker containers. Can restart all containers or specific ones.',
        'parameters': {
            'container_names': {
                'type': 'list or string',
                'description': 'Name(s) of container(s) to restart. Leave empty to restart all.',
                'optional': True
            }
        }
    },
    'get_container_logs': {
        'function': get_container_logs,
        'description': 'Get recent logs from a specific Docker container',
        'parameters': {
            'container_name': {
                'type': 'string',
                'description': 'Name of the container to get logs from',
                'required': True
            },
            'lines': {
                'type': 'integer',
                'description': 'Number of log lines to retrieve (default: 50)',
                'optional': True
            }
        }
    },
    'get_system_stats': {
        'function': get_system_stats,
        'description': 'Get real-time resource usage statistics for all containers (CPU, memory, network, etc.)',
        'parameters': {}
    },
    'execute_network_scan': {
        'function': execute_network_scan,
        'description': 'Execute a network scan using nmap on the CybICS network',
        'parameters': {
            'target': {
                'type': 'string',
                'description': 'Target IP address or network range (e.g., "10.0.0.0/24")',
                'required': True
            },
            'scan_type': {
                'type': 'string',
                'description': 'Type of scan: "basic" (ping scan), "port" (all ports), "service" (version detection), "vuln" (vulnerability scan)',
                'optional': True
            }
        }
    },
    'list_docker_images': {
        'function': list_docker_images,
        'description': 'List all Docker images available on the system',
        'parameters': {}
    }
}


def execute_tool(tool_name, parameters=None):
    """Execute a tool function with given parameters"""
    if tool_name not in AVAILABLE_TOOLS:
        return {'error': f'Unknown tool: {tool_name}'}

    tool = AVAILABLE_TOOLS[tool_name]
    func = tool['function']

    try:
        if parameters:
            result = func(**parameters)
        else:
            result = func()
        return result
    except TypeError as e:
        return {'error': f'Invalid parameters for {tool_name}: {str(e)}'}
    except Exception as e:
        return {'error': f'Error executing {tool_name}: {str(e)}'}


def parse_tool_calls(response_text):
    """
    Parse tool calls from LLM response.
    Looks for patterns like: USE_TOOL: tool_name(param1="value", param2="value")
    """
    tool_calls = []

    # Pattern to match: USE_TOOL: function_name(arg1="value", arg2=123)
    pattern = r'USE_TOOL:\s*(\w+)\((.*?)\)'
    matches = re.finditer(pattern, response_text, re.MULTILINE)

    for match in matches:
        tool_name = match.group(1)
        params_str = match.group(2)

        # Parse parameters
        parameters = {}
        if params_str.strip():
            # Simple parameter parsing (key="value" or key=value)
            param_pattern = r'(\w+)=("[^"]*"|\'[^\']*\'|\d+|true|false|null)'
            param_matches = re.finditer(param_pattern, params_str)

            for param_match in param_matches:
                key = param_match.group(1)
                value = param_match.group(2)

                # Clean up the value
                if value.startswith('"') or value.startswith("'"):
                    value = value[1:-1]  # Remove quotes
                elif value.isdigit():
                    value = int(value)
                elif value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                elif value == 'null':
                    value = None

                parameters[key] = value

        tool_calls.append({
            'tool': tool_name,
            'parameters': parameters
        })

    return tool_calls


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


def format_tool_for_markdown(tool_name, tool_info):
    """Format tool description as markdown"""
    md = f"**{tool_name}**: {tool_info['description']}\n"
    if tool_info['parameters']:
        md += "  - Parameters:\n"
        for param_name, param_info in tool_info['parameters'].items():
            req = "required" if param_info.get('required') else "optional"
            md += f"    - `{param_name}` ({param_info['type']}, {req}): {param_info['description']}\n"
    return md


def format_tool_result_for_llm(tool_name, result):
    """
    Format tool results in a more readable way for the LLM to process
    This helps the LLM generate better markdown responses
    """
    if 'error' in result:
        return f"❌ **Error**: {result['error']}"

    # Format based on tool type
    if tool_name == 'get_container_status':
        if result.get('success') and 'containers' in result:
            containers = result['containers']
            formatted = f"**Container Status** ({len(containers)} running)\n\n"
            formatted += "| Container | Status | Image |\n"
            formatted += "|-----------|--------|-------|\n"
            for c in containers:
                name = c.get('Names', 'unknown')
                status = c.get('Status', 'unknown')
                image = c.get('Image', 'unknown')
                formatted += f"| `{name}` | {status} | `{image}` |\n"
            return formatted

    elif tool_name == 'get_system_stats':
        if result.get('success') and 'container_stats' in result:
            stats = result['container_stats']
            formatted = f"**System Statistics** ({len(stats)} containers)\n\n"
            formatted += "| Container | CPU % | Memory Usage | Network I/O |\n"
            formatted += "|-----------|-------|--------------|-------------|\n"
            for s in stats:
                name = s.get('Name', 'unknown')
                cpu = s.get('CPUPerc', 'N/A')
                mem = s.get('MemUsage', 'N/A')
                net = s.get('NetIO', 'N/A')
                formatted += f"| `{name}` | {cpu} | {mem} | {net} |\n"
            return formatted

    elif tool_name == 'restart_containers':
        if result.get('success'):
            restarted = result.get('restarted', [])
            formatted = f"✅ **Successfully restarted {len(restarted)} container(s)**\n\n"
            for c in restarted:
                formatted += f"- `{c}`\n"
            return formatted
        else:
            failed = result.get('failed', [])
            succeeded = result.get('restarted', [])
            formatted = f"⚠️ **Partial success**: {len(succeeded)} restarted, {len(failed)} failed\n\n"
            if succeeded:
                formatted += "**Restarted**:\n"
                for c in succeeded:
                    formatted += f"- ✅ `{c}`\n"
            if failed:
                formatted += "\n**Failed**:\n"
                for c in failed:
                    formatted += f"- ❌ `{c}`\n"
            return formatted

    elif tool_name == 'get_container_logs':
        if result.get('success'):
            container = result.get('container', 'unknown')
            logs = result.get('logs', '')
            # Truncate very long logs
            if len(logs) > 2000:
                logs = logs[-2000:] + "\n... (truncated)"
            formatted = f"**Logs from** `{container}`\n\n```\n{logs}\n```"
            return formatted

    elif tool_name == 'list_docker_images':
        if result.get('success') and 'images' in result:
            images = result['images']
            formatted = f"**Docker Images** ({len(images)} total)\n\n"
            formatted += "| Repository | Tag | Size |\n"
            formatted += "|------------|-----|------|\n"
            for img in images[:20]:  # Limit to first 20
                repo = img.get('Repository', 'unknown')
                tag = img.get('Tag', 'unknown')
                size = img.get('Size', 'unknown')
                formatted += f"| `{repo}` | `{tag}` | {size} |\n"
            if len(images) > 20:
                formatted += f"\n... and {len(images) - 20} more"
            return formatted

    elif tool_name == 'execute_network_scan':
        if result.get('success'):
            scan_type = result.get('scan_type', 'unknown')
            target = result.get('target', 'unknown')
            results = result.get('results', '')
            # Truncate very long results
            if len(results) > 1500:
                results = results[:1500] + "\n... (truncated)"
            formatted = f"**Network Scan Results**\n\n"
            formatted += f"- **Type**: {scan_type}\n"
            formatted += f"- **Target**: `{target}`\n\n"
            formatted += f"```\n{results}\n```"
            return formatted

    # Default: return JSON
    return f"```json\n{json.dumps(result, indent=2)}\n```"


def generate_response(question, context):
    """Generate response using Ollama - simplified for small models"""
    try:
        # Build prompt with context
        context_str = "\n\n".join(context) if context else "No specific context available."

        prompt = f"""You are the CybICS AI Assistant, an expert on Industrial Control Systems.

Context from documentation:
{context_str}

User Question: {question}

Instructions:
- Answer based on the context provided
- Use markdown formatting: **bold**, `code`, bullet points, tables
- Be clear and concise
- If you don't know, say so

Answer:"""

        # Call Ollama with current model
        response = ollama.chat(
            model=current_model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are the CybICS AI Assistant. Answer questions clearly and concisely using markdown formatting.'
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
        return f"⚠️ **Error**: I'm having trouble connecting to the AI model.\n\n`{str(e)}`"


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model': current_model,
        'knowledge_base_docs': collection.count() if collection else 0
    })


def detect_tool_intent(question):
    """
    Detect if the user's question requires tool execution based on keywords.
    Returns tuple: (should_use_tool, tool_name, parameters)
    """
    question_lower = question.lower()

    # Container status queries
    if any(word in question_lower for word in ['status', 'running', 'list container', 'show container', 'which container']):
        return (True, 'get_container_status', {})

    # Restart containers
    if 'restart' in question_lower:
        # Check if specific container mentioned
        for container in ['openplc', 'fuxa', 'hwio', 'opcua', 's7com', 'landing', 'cybicsagent', 'engineeringws', 'attack']:
            if container in question_lower:
                return (True, 'restart_containers', {'container_names': container})
        return (True, 'restart_containers', {})

    # System stats
    if any(word in question_lower for word in ['cpu', 'memory', 'stats', 'resource', 'performance', 'usage']):
        return (True, 'get_system_stats', {})

    # Logs
    if 'log' in question_lower:
        # Try to find container name
        for container in ['openplc', 'fuxa', 'hwio', 'opcua', 's7com', 'landing', 'cybicsagent', 'engineeringws', 'attack']:
            if container in question_lower:
                # Check for line count
                import re
                lines_match = re.search(r'(\d+)\s*lines?', question_lower)
                lines = int(lines_match.group(1)) if lines_match else 50
                return (True, 'get_container_logs', {'container_name': container, 'lines': lines})
        return (False, None, {})

    # Network scan
    if any(word in question_lower for word in ['scan', 'nmap', 'network']):
        import re
        # Try to extract IP/network
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?:/\d+)?)', question)
        target = ip_match.group(1) if ip_match else '172.18.0.0/24'

        scan_type = 'basic'
        if 'port' in question_lower:
            scan_type = 'port'
        elif 'service' in question_lower or 'version' in question_lower:
            scan_type = 'service'
        elif 'vuln' in question_lower or 'vulnerability' in question_lower:
            scan_type = 'vuln'

        return (True, 'execute_network_scan', {'target': target, 'scan_type': scan_type})

    # Docker images
    if any(word in question_lower for word in ['image', 'docker image']):
        return (True, 'list_docker_images', {})

    return (False, None, {})


@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint with tool calling support"""
    try:
        data = request.get_json()
        question = data.get('message', '').strip()

        if not question:
            return jsonify({'error': 'No message provided'}), 400

        logger.info(f"Received question: {question}")

        # First, check if the question requires a tool (keyword-based detection)
        should_use_tool, tool_name, tool_params = detect_tool_intent(question)

        if should_use_tool:
            logger.info(f"Detected tool intent: {tool_name} with params {tool_params}")

            # Execute the tool
            result = execute_tool(tool_name, tool_params)

            # Format the result
            formatted_result = format_tool_result_for_llm(tool_name, result)

            # Generate natural language response based on tool result
            final_prompt = f"""The user asked: "{question}"

I executed the tool `{tool_name}` and got these results:

{formatted_result}

Provide a clear, helpful markdown response summarizing what was found. Be concise and well-formatted."""

            final_response = ollama.chat(
                model=current_model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are the CybICS AI Assistant. Provide concise, well-formatted markdown responses based on tool results.'
                    },
                    {
                        'role': 'user',
                        'content': final_prompt
                    }
                ]
            )

            response = final_response['message']['content']

            return jsonify({
                'response': response,
                'sources': 0,
                'tools_used': [tool_name],
                'tool_results': [{
                    'tool': tool_name,
                    'parameters': tool_params,
                    'result': result
                }]
            })

        # If no tool needed, use knowledge base RAG
        context = query_knowledge_base(question)

        # Generate initial response
        response = generate_response(question, context)
        logger.info(f"Initial response: {response[:200]}...")

        # Check if response contains tool calls (fallback for USE_TOOL syntax)
        tool_calls = parse_tool_calls(response)

        if tool_calls:
            logger.info(f"Detected {len(tool_calls)} tool call(s)")

            # Execute all tool calls
            tool_results = []
            for call in tool_calls:
                tool_name = call['tool']
                parameters = call['parameters']

                logger.info(f"Executing tool: {tool_name} with params: {parameters}")
                result = execute_tool(tool_name, parameters)
                tool_results.append({
                    'tool': tool_name,
                    'parameters': parameters,
                    'result': result
                })

            # Generate final response with tool results (formatted for better readability)
            tool_results_str = "\n\n---\n\n".join([
                f"**Tool**: `{tr['tool']}`\n**Parameters**: {json.dumps(tr['parameters']) if tr['parameters'] else 'none'}\n\n**Result**:\n{format_tool_result_for_llm(tr['tool'], tr['result'])}"
                for tr in tool_results
            ])

            final_prompt = f"""Based on the tool execution results below, provide a clear and helpful answer to the user's question.

Original Question: {question}

Tool Execution Results:
{tool_results_str}

IMPORTANT: Your response will be rendered as Markdown. Provide a well-formatted response:
- Start with a brief summary of what was done
- Use **bold** for important information (container names, status, counts)
- Use `code` formatting for technical terms, IPs, and names
- Use bullet points or tables for listing items
- Use code blocks for logs or detailed output
- Be concise but informative
- If there are errors, highlight them clearly

Provide a natural language markdown response summarizing the results:"""

            final_response = ollama.chat(
                model=current_model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are the CybICS AI Assistant. Provide well-formatted markdown responses that summarize tool results clearly and professionally.'
                    },
                    {
                        'role': 'user',
                        'content': final_prompt
                    }
                ]
            )

            response = final_response['message']['content']

            return jsonify({
                'response': response,
                'sources': len(context),
                'tools_used': [tr['tool'] for tr in tool_results],
                'tool_results': tool_results
            })
        else:
            # No tool calls, return the response as-is
            return jsonify({
                'response': response,
                'sources': len(context)
            })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
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
            'version': '2.1.0',
            'model': current_model,
            'default_model': OLLAMA_MODEL,
            'available_models': models,
            'knowledge_base_docs': collection.count() if collection else 0,
            'available_tools': len(AVAILABLE_TOOLS),
            'status': 'ready',
            'capabilities': [
                'Knowledge Base Q&A',
                'Intelligent Tool Detection',
                'Container Management',
                'System Monitoring',
                'Network Scanning',
                'Log Analysis'
            ]
        })
    except Exception as e:
        logger.error(f"Error in info endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tools', methods=['GET'])
def list_tools():
    """List all available tools with their descriptions"""
    try:
        tools_list = []
        for tool_name, tool_info in AVAILABLE_TOOLS.items():
            tools_list.append({
                'name': tool_name,
                'description': tool_info['description'],
                'parameters': tool_info['parameters']
            })

        return jsonify({
            'tools': tools_list,
            'total': len(tools_list)
        })
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/model', methods=['GET'])
def get_model():
    """Get current model information"""
    try:
        # Get list of available models
        models = []
        try:
            models_response = ollama.list()
            models = [m['name'] for m in models_response.get('models', [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")

        return jsonify({
            'current_model': current_model,
            'default_model': OLLAMA_MODEL,
            'available_models': models,
            'recommended_models': [
                {
                    'name': 'tinyllama',
                    'size': '600MB',
                    'quality': 2,
                    'description': 'Ultra-lightweight, fast responses'
                },
                {
                    'name': 'phi3:mini',
                    'size': '2.3GB',
                    'quality': 4,
                    'description': 'Recommended - Best balance of size and quality',
                    'recommended': True
                },
                {
                    'name': 'llama3.2:3b',
                    'size': '2GB',
                    'quality': 4,
                    'description': 'Excellent quality, lightweight'
                },
                {
                    'name': 'mistral:7b',
                    'size': '4.1GB',
                    'quality': 5,
                    'description': 'High quality responses'
                },
                {
                    'name': 'llama3.1:8b',
                    'size': '4.7GB',
                    'quality': 5,
                    'description': 'Best quality, most resource intensive'
                }
            ]
        })
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/model', methods=['POST'])
def set_model():
    """Change the current model"""
    global current_model

    try:
        data = request.get_json()
        new_model = data.get('model', '').strip()

        if not new_model:
            return jsonify({'error': 'No model specified'}), 400

        logger.info(f"Changing model from {current_model} to {new_model}")

        # Check if model exists, if not try to pull it
        try:
            # Try a simple chat to verify model works
            ollama.chat(
                model=new_model,
                messages=[{'role': 'user', 'content': 'test'}]
            )

            # Model works, update current model
            current_model = new_model
            logger.info(f"Successfully changed model to {new_model}")

            return jsonify({
                'success': True,
                'model': current_model,
                'message': f'Model changed to {new_model}'
            })

        except Exception as e:
            error_str = str(e)

            # Check if it's a "model not found" error
            if 'not found' in error_str.lower() or 'pull' in error_str.lower():
                logger.info(f"Model {new_model} not found, attempting to pull...")

                # Try to pull the model
                try:
                    logger.info(f"Pulling model {new_model}... This may take several minutes.")

                    # Actually pull the model (this is blocking)
                    ollama.pull(new_model)

                    logger.info(f"Successfully downloaded model {new_model}")

                    # Now try to use it and switch to it
                    try:
                        ollama.chat(
                            model=new_model,
                            messages=[{'role': 'user', 'content': 'test'}]
                        )

                        # Model works, update current model
                        current_model = new_model
                        logger.info(f"Successfully changed model to {new_model}")

                        return jsonify({
                            'success': True,
                            'model': current_model,
                            'message': f'Model {new_model} downloaded and activated successfully',
                            'downloaded': True
                        })

                    except Exception as test_error:
                        logger.error(f"Model downloaded but failed to activate: {test_error}")
                        return jsonify({
                            'success': False,
                            'error': f'Model downloaded but failed to activate: {str(test_error)}'
                        }), 500

                except Exception as pull_error:
                    logger.error(f"Error pulling model {new_model}: {pull_error}")
                    return jsonify({
                        'success': False,
                        'error': f'Failed to download model: {str(pull_error)}'
                    }), 500
            else:
                logger.error(f"Error setting model: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

    except Exception as e:
        logger.error(f"Error in set_model endpoint: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/model/pull', methods=['POST'])
def pull_model():
    """Download a model (non-blocking status check)"""
    try:
        data = request.get_json()
        model_name = data.get('model', '').strip()

        if not model_name:
            return jsonify({'error': 'No model specified'}), 400

        logger.info(f"Initiating pull for model: {model_name}")

        # Start pulling the model
        try:
            ollama.pull(model_name)
            return jsonify({
                'success': True,
                'message': f'Model {model_name} downloaded successfully',
                'model': model_name
            })
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Error in pull_model endpoint: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting CybICS AI Agent...")
    logger.info(f"Using Ollama model: {OLLAMA_MODEL}")
    logger.info(f"Ollama host: {OLLAMA_HOST}")

    # Initialize knowledge base
    initialize_knowledge_base()

    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
