"""CybICS AI Agent - Flask route handlers"""
import json
import logging

from flask import request, jsonify, Response, url_for
import ollama

import config
from tools import AVAILABLE_TOOLS, execute_tool, get_ollama_tool_schemas
from tools.formatters import format_tool_for_markdown, format_tool_result_for_llm
from rag import get_collection
from agent import process_chat, SYSTEM_PROMPT
from session import session_manager

logger = logging.getLogger(__name__)


# OpenAPI specification (generated dynamically)
def _get_openapi_spec():
    """Generate OpenAPI 3.0 specification for the CybICS AI Agent API."""
    schemes = get_ollama_tool_schemas()
    
    # Build tool schemas for OpenAPI
    tool_components = {}
    for schema in schemes:
        tool_name = schema['function']['name']
        tool_components[tool_name] = {
            'type': 'object',
            'properties': schema['function']['parameters']['properties'],
            'required': schema['function']['parameters'].get('required', []),
            'description': schema['function']['description']
        }
    
    # Build paths
    paths = {
        '/': {
            'get': {
                'tags': ['Info'],
                'summary': 'API root',
                'description': 'Returns basic API information and links to documentation',
                'responses': {
                    '200': {
                        'description': 'API info',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'message': {'type': 'string', 'example': 'CybICS AI Agent API'},
                                        'version': {'type': 'string', 'example': '3.0.0'},
                                        'docs': {'type': 'string', 'format': 'uri'},
                                        'health': {'type': 'string', 'format': 'uri'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        '/api/docs': {
            'get': {
                'tags': ['Info'],
                'summary': 'OpenAPI specification',
                'description': 'Returns the complete OpenAPI 3.0 specification for this API',
                'responses': {
                    '200': {
                        'description': 'OpenAPI specification in JSON format',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'openapi': {'type': 'string', 'example': '3.0.0'},
                                        'info': {'type': 'object'},
                                        'paths': {'type': 'object'},
                                        'components': {'type': 'object'}
                                    }
                                }
                            }
                        }
                    },
                    '500': {'description': 'Failed to generate specification'}
                }
            }
        },
        '/health': {
            'get': {
                'tags': ['Health'],
                'summary': 'Health check endpoint',
                'description': 'Returns the health status of the AI agent service',
                'responses': {
                    '200': {
                        'description': 'Service is healthy',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'status': {'type': 'string', 'example': 'healthy'},
                                        'model': {'type': 'string', 'example': 'phi3:mini'},
                                        'knowledge_base_docs': {'type': 'integer', 'example': 42}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        '/api/chat': {
            'post': {
                'tags': ['Chat'],
                'summary': 'Process a chat message',
                'description': 'Send a chat message and receive an AI response with optional tool execution',
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'required': ['message'],
                                'properties': {
                                    'message': {'type': 'string', 'description': 'The user message or question'},
                                    'session_id': {'type': 'string', 'description': 'Optional session ID for conversation history'}
                                }
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'Chat response',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'response': {'type': 'string', 'description': 'The AI response text'},
                                        'session_id': {'type': 'string', 'description': 'The session ID'},
                                        'sources': {'type': 'integer', 'description': 'Number of RAG sources used'},
                                        'tools_used': {'type': 'array', 'items': {'type': 'string'}},
                                        'tool_results': {'type': 'array', 'items': {'type': 'object'}},
                                        'confirmation_required': {'type': 'boolean'}
                                    }
                                }
                            }
                        }
                    },
                    '400': {'description': 'No message provided'}
                }
            }
        },
        '/api/chat/stream': {
            'post': {
                'tags': ['Chat'],
                'summary': 'Stream chat response via SSE',
                'description': 'Returns a Server-Sent Events stream for real-time chat responses',
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'required': ['message'],
                                'properties': {
                                    'message': {'type': 'string', 'description': 'The user message or question'},
                                    'session_id': {'type': 'string', 'description': 'Optional session ID for conversation history'}
                                }
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'SSE stream',
                        'content': {
                            'text/event-stream': {
                                'schema': {
                                    'type': 'string',
                                    'format': 'binary'
                                }
                            }
                        }
                    },
                    '400': {'description': 'No message provided'},
                    '503': {'description': 'Agent service unavailable'}
                }
            }
        },
        '/api/info': {
            'get': {
                'tags': ['Info'],
                'summary': 'Get agent information',
                'description': 'Returns detailed information about the AI agent',
                'responses': {
                    '200': {
                        'description': 'Agent info',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'name': {'type': 'string', 'example': 'CybICS AI Agent'},
                                        'version': {'type': 'string', 'example': '3.0.0'},
                                        'model': {'type': 'string'},
                                        'default_model': {'type': 'string'},
                                        'available_models': {'type': 'array', 'items': {'type': 'string'}},
                                        'knowledge_base_docs': {'type': 'integer'},
                                        'available_tools': {'type': 'integer'},
                                        'status': {'type': 'string'},
                                        'native_tool_calling': {'type': 'boolean'},
                                        'capabilities': {'type': 'array', 'items': {'type': 'string'}}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        '/api/tools': {
            'get': {
                'tags': ['Tools'],
                'summary': 'List all available tools',
                'description': 'Returns a list of all available ICS tools',
                'responses': {
                    '200': {
                        'description': 'List of tools',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'tools': {
                                            'type': 'array',
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'name': {'type': 'string'},
                                                    'description': {'type': 'string'},
                                                    'parameters': {'type': 'object'},
                                                    'destructive': {'type': 'boolean'}
                                                }
                                            }
                                        },
                                        'total': {'type': 'integer'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        '/api/model': {
            'get': {
                'tags': ['Model'],
                'summary': 'Get current model information',
                'description': 'Returns information about the current and available models',
                'responses': {
                    '200': {
                        'description': 'Model info',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'current_model': {'type': 'string'},
                                        'default_model': {'type': 'string'},
                                        'available_models': {'type': 'array', 'items': {'type': 'string'}},
                                        'native_tool_calling': {'type': 'boolean'},
                                        'recommended_models': {
                                            'type': 'array',
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'name': {'type': 'string'},
                                                    'size': {'type': 'string'},
                                                    'quality': {'type': 'integer'},
                                                    'description': {'type': 'string'},
                                                    'recommended': {'type': 'boolean'}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            'post': {
                'tags': ['Model'],
                'summary': 'Change the current model',
                'description': 'Switch to a different Ollama model',
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'required': ['model'],
                                'properties': {
                                    'model': {'type': 'string', 'description': 'Name of the model to use'}
                                }
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'Model changed successfully',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'success': {'type': 'boolean'},
                                        'model': {'type': 'string'},
                                        'native_tool_calling': {'type': 'boolean'},
                                        'message': {'type': 'string'},
                                        'downloaded': {'type': 'boolean'}
                                    }
                                }
                            }
                        }
                    },
                    '400': {'description': 'No model specified'},
                    '500': {'description': 'Failed to set model'}
                }
            }
        },
        '/api/model/pull': {
            'post': {
                'tags': ['Model'],
                'summary': 'Download a model',
                'description': 'Download a new Ollama model',
                'requestBody': {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'required': ['model'],
                                'properties': {
                                    'model': {'type': 'string', 'description': 'Name of the model to download'}
                                }
                            }
                        }
                    }
                },
                'responses': {
                    '200': {
                        'description': 'Model downloaded',
                        'content': {
                            'application/json': {
                                'schema': {
                                    'type': 'object',
                                    'properties': {
                                        'success': {'type': 'boolean'},
                                        'message': {'type': 'string'},
                                        'model': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    },
                    '400': {'description': 'No model specified'},
                    '500': {'description': 'Failed to download model'}
                }
            }
        }
    }
    
    return {
        'openapi': '3.0.0',
        'info': {
            'title': 'CybICS AI Agent API',
            'description': (
                'The CybICS AI Agent provides an intelligent assistant for the CybICS ICS training platform. '
                'It supports native Ollama tool calling, keyword-based tool dispatch, RAG knowledge base, '
                'conversation history, and streaming responses. The agent includes ICS-specific tools for '
                'interacting with Modbus, OPC-UA, IDS, and the physical process simulation.'
            ),
            'version': '3.0.0',
            'contact': {
                'name': 'CybICS Team',
                'url': 'https://github.com/CybICS/CybICS'
            }
        },
        'servers': [
            {'url': 'http://localhost:5000', 'description': 'Local development'},
            {'url': 'http://172.18.0.11:5000', 'description': 'Docker network'}
        ],
        'tags': [
            {'name': 'Health', 'description': 'Health check endpoints'},
            {'name': 'Chat', 'description': 'Chat and conversation endpoints'},
            {'name': 'Info', 'description': 'Agent information'},
            {'name': 'Tools', 'description': 'Available ICS tools'},
            {'name': 'Model', 'description': 'Model management'}
        ],
        'paths': paths,
        'components': {
            'schemas': tool_components
        }
    }


def register_routes(app):
    """Register all route handlers on the Flask app."""

    @app.route('/')
    def index():
        """Redirect to OpenAPI documentation"""
        return jsonify({
            'message': 'CybICS AI Agent API',
            'version': '3.0.0',
            'docs': url_for('openapi_spec', _external=True),
            'health': url_for('health', _external=True)
        })

    @app.route('/api/docs', methods=['GET'])
    def openapi_spec():
        """Serve OpenAPI 3.0 specification for API documentation"""
        try:
            spec = _get_openapi_spec()
            return jsonify(spec)
        except Exception as e:
            logger.error(f"Error generating OpenAPI spec: {e}")
            return jsonify({'error': 'Failed to generate OpenAPI specification'}), 500

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        from rag import initialize_knowledge_base, get_collection, _init_lock
        coll = get_collection()
        # Lazy initialization on first request (thread-safe)
        if coll is None:
            with _init_lock:
                coll = get_collection()
                if coll is None:
                    initialize_knowledge_base()
                    coll = get_collection()
        return jsonify({
            'status': 'healthy',
            'model': config.current_model(),
            'knowledge_base_docs': coll.count() if coll else 0
        })

    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Chat endpoint with tool calling support"""
        try:
            data = request.get_json()
            question = data.get('message', '').strip()
            session_id = data.get('session_id')

            if not question:
                return jsonify({'error': 'No message provided'}), 400

            logger.info(f"Received question: {question}")

            result = process_chat(question, session_id=session_id)
            return jsonify(result)

        except Exception as e:
            logger.error(f"Error in chat endpoint: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred while processing your message'}), 500

    @app.route('/api/chat/stream', methods=['POST'])
    def chat_stream():
        """Streaming chat endpoint using Server-Sent Events."""
        try:
            data = request.get_json()
            question = data.get('message', '').strip()
            session_id = data.get('session_id')

            if not question:
                return jsonify({'error': 'No message provided'}), 400

            logger.info(f"Stream request: {question}")
            model = config.current_model()

            session = session_manager.get_or_create(session_id)
            sid = session['id']

            # Handle confirmation
            if question.strip() == '__confirm__':
                result = process_chat(question, session_id=sid)
                def confirm_gen():
                    yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
                    yield f"data: {json.dumps({'type': 'content', 'content': result['response']})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'tools_used': result.get('tools_used', [])})}\n\n"
                return Response(confirm_gen(), mimetype='text/event-stream',
                                headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

            session_manager.add_message(sid, 'user', question)

            # Check for tool intent
            from agent import detect_tool_intent
            should_use_tool, tool_name, tool_params = detect_tool_intent(question)

            # For native tool calling models, let them decide
            if config.model_supports_tools(model) and not should_use_tool:
                from agent import SYSTEM_PROMPT
                from rag import query_knowledge_base as rag_query

                # First call: let the model decide if it wants tools (non-streaming)
                history = session_manager.get_messages(sid, model)
                messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
                messages.extend(history)

                context = rag_query(question)
                if context:
                    context_str = "\n\n".join(context)
                    messages[-1] = {
                        'role': 'user',
                        'content': f"Context from CybICS documentation:\n{context_str}\n\nUser question: {question}"
                    }

                tool_schemas = get_ollama_tool_schemas()

                try:
                    response = ollama.chat(model=model, messages=messages, tools=tool_schemas)
                except Exception as e:
                    logger.error(f"Native tool call error in stream: {e}")
                    response = None

                if response and response.message.tool_calls:
                    tools_used = []
                    tool_results_list = []

                    for tool_call in response.message.tool_calls:
                        tn = tool_call.function.name
                        ta = tool_call.function.arguments or {}
                        logger.info(f"Native stream tool call: {tn}({ta})")

                        tool_info_check = AVAILABLE_TOOLS.get(tn, {})
                        if tool_info_check.get('destructive'):
                            session_manager.set_pending_action(sid, tn, ta)
                            from agent import _describe_action
                            desc = _describe_action(tn, ta)
                            def confirm_native_gen():
                                yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
                                msg = f"This action requires confirmation:\n\n**{desc}**\n\nAre you sure you want to proceed?"
                                yield f"data: {json.dumps({'type': 'content', 'content': msg})}\n\n"
                                yield f"data: {json.dumps({'type': 'done', 'confirmation_required': True, 'pending_action': {'tool': tn, 'parameters': ta}})}\n\n"
                            return Response(confirm_native_gen(), mimetype='text/event-stream',
                                            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

                        result = execute_tool(tn, ta)
                        tools_used.append(tn)
                        tool_results_list.append({'tool': tn, 'parameters': ta, 'result': result})

                    # Build messages for streaming summary
                    messages.append(response.message)
                    for tr in tool_results_list:
                        formatted = format_tool_result_for_llm(tr['tool'], tr['result'])
                        messages.append({'role': 'tool', 'content': formatted})

                    def native_tool_stream_gen():
                        yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
                        for tn in tools_used:
                            yield f"data: {json.dumps({'type': 'tool', 'tool': tn})}\n\n"

                        full_response = []
                        try:
                            stream = ollama.chat(model=model, messages=messages, stream=True)
                            for chunk in stream:
                                token = chunk.message.content
                                if token:
                                    full_response.append(token)
                                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                        except Exception as e:
                            logger.error(f"Native tool stream error: {e}")
                            fallback = "\n\n".join(
                                format_tool_result_for_llm(tr['tool'], tr['result'])
                                for tr in tool_results_list
                            )
                            full_response.append(fallback)
                            yield f"data: {json.dumps({'type': 'content', 'content': fallback})}\n\n"

                        response_text = ''.join(full_response)
                        session_manager.add_message(sid, 'assistant', response_text)
                        yield f"data: {json.dumps({'type': 'done', 'tools_used': tools_used})}\n\n"

                    return Response(native_tool_stream_gen(), mimetype='text/event-stream',
                                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

            if should_use_tool:
                # Check destructive
                tool_info = AVAILABLE_TOOLS.get(tool_name, {})
                if tool_info.get('destructive'):
                    session_manager.set_pending_action(sid, tool_name, tool_params)
                    from agent import _describe_action
                    desc = _describe_action(tool_name, tool_params)
                    def confirm_prompt_gen():
                        yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
                        msg = f"This action requires confirmation:\n\n**{desc}**\n\nAre you sure you want to proceed?"
                        yield f"data: {json.dumps({'type': 'content', 'content': msg})}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'confirmation_required': True, 'pending_action': {'tool': tool_name, 'parameters': tool_params}})}\n\n"
                    return Response(confirm_prompt_gen(), mimetype='text/event-stream',
                                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

                # Execute tool, then stream LLM summary
                result = execute_tool(tool_name, tool_params)
                formatted = format_tool_result_for_llm(tool_name, result)

                def tool_stream_gen():
                    yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
                    yield f"data: {json.dumps({'type': 'tool', 'tool': tool_name})}\n\n"

                    prompt = (
                        f'The user asked: "{question}"\n\n'
                        f'I executed `{tool_name}` and got:\n\n{formatted}\n\n'
                        f'Provide a clear, helpful markdown response. Be concise.'
                    )

                    full_response = []
                    try:
                        stream = ollama.chat(
                            model=model,
                            messages=[
                                {'role': 'system', 'content': SYSTEM_PROMPT},
                                {'role': 'user', 'content': prompt},
                            ],
                            stream=True,
                        )
                        for chunk in stream:
                            token = chunk.message.content
                            if token:
                                full_response.append(token)
                                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    except Exception as e:
                        logger.error(f"Stream error: {e}")
                        full_response.append(formatted)
                        yield f"data: {json.dumps({'type': 'content', 'content': formatted})}\n\n"

                    response_text = ''.join(full_response)
                    session_manager.add_message(sid, 'assistant', response_text)
                    yield f"data: {json.dumps({'type': 'done', 'tools_used': [tool_name]})}\n\n"

                return Response(tool_stream_gen(), mimetype='text/event-stream',
                                headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

            # No tool — stream RAG response
            from rag import query_knowledge_base
            context = query_knowledge_base(question)
            context_str = "\n\n".join(context) if context else "No specific context available."

            def rag_stream_gen():
                yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"

                prompt = (
                    f"Context from CybICS documentation:\n{context_str}\n\n"
                    f"User Question: {question}\n\n"
                    f"Answer clearly and concisely using markdown formatting."
                )

                full_response = []
                try:
                    stream = ollama.chat(
                        model=model,
                        messages=[
                            {'role': 'system', 'content': SYSTEM_PROMPT},
                            {'role': 'user', 'content': prompt},
                        ],
                        stream=True,
                    )
                    for chunk in stream:
                        token = chunk.message.content
                        if token:
                            full_response.append(token)
                            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                except Exception as e:
                    logger.error(f"Stream error: {e}")
                    yield f"data: {json.dumps({'type': 'content', 'content': 'Error generating response.'})}\n\n"

                response_text = ''.join(full_response)
                session_manager.add_message(sid, 'assistant', response_text)
                yield f"data: {json.dumps({'type': 'done', 'sources': len(context)})}\n\n"

            return Response(rag_stream_gen(), mimetype='text/event-stream',
                            headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

        except Exception as e:
            logger.error(f"Error in stream endpoint: {e}", exc_info=True)
            return jsonify({'error': 'An internal error occurred'}), 500

    @app.route('/api/info', methods=['GET'])
    def info():
        """Get agent information"""
        try:
            models = []
            try:
                models_response = ollama.list()
                models = [m.model for m in models_response.models]
            except Exception:
                pass

            coll = get_collection()
            current = config.current_model()
            return jsonify({
                'name': 'CybICS AI Agent',
                'version': '3.0.0',
                'model': current,
                'default_model': config.OLLAMA_MODEL,
                'available_models': models,
                'knowledge_base_docs': coll.count() if coll else 0,
                'available_tools': len(AVAILABLE_TOOLS),
                'status': 'ready',
                'native_tool_calling': config.model_supports_tools(current),
                'capabilities': [
                    'Interactive Training Coach',
                    'CTF Progress Tracking',
                    'Defense Challenge Verification',
                    'Live Process Monitoring',
                    'Network Traffic Analysis',
                    'IDS Forensics Assistant',
                    'Knowledge Base Q&A',
                    'Native Tool Calling',
                    'Keyword Tool Detection (fallback)',
                    'Container Management',
                    'System Monitoring',
                    'Network Scanning',
                    'Modbus Register Reading',
                    'OPC-UA Node Browsing',
                    'IDS Alert Monitoring',
                    'Conversation History',
                    'Streaming Responses',
                ]
            })
        except Exception as e:
            logger.error(f"Error in info endpoint: {e}")
            return jsonify({'error': 'An internal error occurred while retrieving agent information'}), 500

    @app.route('/api/tools', methods=['GET'])
    def list_tools():
        """List all available tools with their descriptions"""
        try:
            tools_list = []
            for tool_name, tool_info in AVAILABLE_TOOLS.items():
                tools_list.append({
                    'name': tool_name,
                    'description': tool_info['description'],
                    'parameters': tool_info['parameters'],
                    'destructive': tool_info.get('destructive', False),
                })

            return jsonify({
                'tools': tools_list,
                'total': len(tools_list)
            })
        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return jsonify({'error': 'An internal error occurred while listing tools'}), 500

    @app.route('/api/model', methods=['GET'])
    def get_model():
        """Get current model information"""
        try:
            models = []
            try:
                models_response = ollama.list()
                models = [m.model for m in models_response.models]
            except Exception as e:
                logger.error(f"Error listing models: {e}")

            current = config.current_model()
            return jsonify({
                'current_model': current,
                'default_model': config.OLLAMA_MODEL,
                'available_models': models,
                'native_tool_calling': config.model_supports_tools(current),
                'recommended_models': [
                    {
                        'name': 'phi3:mini',
                        'size': '2.3GB',
                        'quality': 4,
                        'description': 'Recommended - Good balance, native tool calling',
                        'recommended': True,
                    },
                    {
                        'name': 'llama3.2:3b',
                        'size': '2GB',
                        'quality': 4,
                        'description': 'Excellent quality, native tool calling',
                    },
                    {
                        'name': 'mistral:7b',
                        'size': '4.1GB',
                        'quality': 5,
                        'description': 'High quality, native tool calling',
                    },
                    {
                        'name': 'llama3.1:8b',
                        'size': '4.7GB',
                        'quality': 5,
                        'description': 'Best quality, most resource intensive',
                    },
                ]
            })
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return jsonify({'error': 'An internal error occurred while retrieving model information'}), 500

    @app.route('/api/model', methods=['POST'])
    def set_model():
        """Change the current model"""
        try:
            data = request.get_json()
            new_model = data.get('model', '').strip()

            if not new_model:
                return jsonify({'error': 'No model specified'}), 400

            current_before = config.current_model()
            logger.info(f"Changing model from {current_before} to {new_model}")

            try:
                ollama.chat(
                    model=new_model,
                    messages=[{'role': 'user', 'content': 'test'}]
                )

                config.set_current_model(new_model)
                logger.info(f"Successfully changed model to {new_model}")

                return jsonify({
                    'success': True,
                    'model': config.current_model(),
                    'native_tool_calling': config.model_supports_tools(new_model),
                    'message': f'Model changed to {new_model}'
                })

            except Exception as e:
                error_str = str(e)

                if 'not found' in error_str.lower() or 'pull' in error_str.lower():
                    logger.info(f"Model {new_model} not found, attempting to pull...")

                    try:
                        ollama.pull(new_model)
                        logger.info(f"Successfully downloaded model {new_model}")

                        try:
                            ollama.chat(
                                model=new_model,
                                messages=[{'role': 'user', 'content': 'test'}]
                            )
                            config.set_current_model(new_model)
                            logger.info(f"Successfully changed model to {new_model}")

                            return jsonify({
                                'success': True,
                                'model': config.current_model(),
                                'native_tool_calling': config.model_supports_tools(new_model),
                                'message': f'Model {new_model} downloaded and activated successfully',
                                'downloaded': True
                            })

                        except Exception as test_error:
                            logger.error(f"Model downloaded but failed to activate: {test_error}")
                            return jsonify({
                                'success': False,
                                'error': 'Model downloaded but failed to activate'
                            }), 500

                    except Exception as pull_error:
                        logger.error(f"Error pulling model {new_model}: {pull_error}")
                        return jsonify({
                            'success': False,
                            'error': 'Failed to download the requested model'
                        }), 500
                else:
                    logger.error(f"Error setting model: {e}")
                    return jsonify({
                        'success': False,
                        'error': 'Failed to set the specified model'
                    }), 500

        except Exception as e:
            logger.error(f"Error in set_model endpoint: {e}")
            return jsonify({'error': 'An internal error occurred while setting the model'}), 500

    @app.route('/api/model/pull', methods=['POST'])
    def pull_model():
        """Download a model"""
        try:
            data = request.get_json()
            model_name = data.get('model', '').strip()

            if not model_name:
                return jsonify({'error': 'No model specified'}), 400

            logger.info(f"Initiating pull for model: {model_name}")

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
                    'error': 'Failed to download the specified model'
                }), 500

        except Exception as e:
            logger.error(f"Error in pull_model endpoint: {e}")
            return jsonify({'error': 'An internal error occurred while pulling the model'}), 500
