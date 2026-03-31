"""CybICS AI Agent - Flask route handlers"""
import json
import logging

from flask import request, jsonify, Response
import ollama

import config
from tools import AVAILABLE_TOOLS, execute_tool
from tools.formatters import format_tool_for_markdown, format_tool_result_for_llm
from rag import get_collection
from agent import process_chat, SYSTEM_PROMPT
from session import session_manager

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all route handlers on the Flask app."""

    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        coll = get_collection()
        return jsonify({
            'status': 'healthy',
            'model': config.current_model,
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
            model = config.current_model

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
                # Try native tool calling first (non-streaming), then stream the summary
                from agent import _native_tool_dispatch
                result = _native_tool_dispatch(question, sid, model)
                if result.get('tools_used'):
                    def native_tool_gen():
                        yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"
                        for tn in result.get('tools_used', []):
                            yield f"data: {json.dumps({'type': 'tool', 'tool': tn})}\n\n"
                        yield f"data: {json.dumps({'type': 'content', 'content': result['response']})}\n\n"
                        session_manager.add_message(sid, 'assistant', result['response'])
                        yield f"data: {json.dumps({'type': 'done', 'tools_used': result.get('tools_used', [])})}\n\n"
                    return Response(native_tool_gen(), mimetype='text/event-stream',
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
            return jsonify({
                'name': 'CybICS AI Agent',
                'version': '3.0.0',
                'model': config.current_model,
                'default_model': config.OLLAMA_MODEL,
                'available_models': models,
                'knowledge_base_docs': coll.count() if coll else 0,
                'available_tools': len(AVAILABLE_TOOLS),
                'status': 'ready',
                'native_tool_calling': config.model_supports_tools(config.current_model),
                'capabilities': [
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

            return jsonify({
                'current_model': config.current_model,
                'default_model': config.OLLAMA_MODEL,
                'available_models': models,
                'native_tool_calling': config.model_supports_tools(config.current_model),
                'recommended_models': [
                    {
                        'name': 'tinyllama',
                        'size': '600MB',
                        'quality': 2,
                        'description': 'Ultra-lightweight, fast responses (keyword tool dispatch)',
                    },
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

            logger.info(f"Changing model from {config.current_model} to {new_model}")

            try:
                ollama.chat(
                    model=new_model,
                    messages=[{'role': 'user', 'content': 'test'}]
                )

                config.current_model = new_model
                logger.info(f"Successfully changed model to {new_model}")

                return jsonify({
                    'success': True,
                    'model': config.current_model,
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
                            config.current_model = new_model
                            logger.info(f"Successfully changed model to {new_model}")

                            return jsonify({
                                'success': True,
                                'model': config.current_model,
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
