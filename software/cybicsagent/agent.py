"""CybICS AI Agent - Core agent logic (dual-mode tool dispatch)"""
import re
import json
import logging

import ollama

import config
from tools import AVAILABLE_TOOLS, execute_tool, get_ollama_tool_schemas
from tools.formatters import format_tool_result_for_llm
from rag import query_knowledge_base
from session import session_manager

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    'You are the CybICS AI Training Coach, an expert on Industrial Control Systems (ICS) '
    'and SCADA cybersecurity. Your primary role is to help students learn ICS security '
    'through the CybICS training platform.\n\n'
    'When helping with training:\n'
    '- Guide students step-by-step through exercises rather than giving away answers\n'
    '- Use progressive hints: start vague, get more specific if they are stuck\n'
    '- Explain the security concepts behind each exercise (MITRE ATT&CK for ICS)\n'
    '- Use live system tools to demonstrate concepts with real data\n'
    '- Check their CTF progress to suggest appropriate next challenges\n'
    '- When they complete an attack, show the effect on the physical process\n'
    '- For defense challenges, verify their work and explain what passed/failed\n\n'
    'You have tools to read live Modbus registers, monitor tank pressures, '
    'analyze network traffic, check IDS alerts, and track CTF progress. '
    'Use these to make learning interactive and hands-on.\n\n'
    'Answer clearly and concisely using markdown formatting. '
    'When you use tools, explain what the results mean for the student\'s learning.\n\n'
    'IMPORTANT RULES:\n'
    '- NEVER include URLs or hyperlinks in your responses. No markdown links.\n'
    '- Refer to training modules by name only (e.g. "the PLC programming module").\n'
    '- Do NOT invent or hallucinate URLs. There are no web links to provide.\n'
    '- If the student wants more info on a module, tell them to ask you about it.'
)


def process_chat(question, session_id=None):
    """
    Process a chat message. Returns a response dict.

    Uses native Ollama tool calling for capable models,
    falls back to keyword-based dispatch for models without native tool calling.
    """
    model = config.current_model()
    session = session_manager.get_or_create(session_id)
    sid = session['id']

    # Handle confirmation of pending destructive action
    if question.strip() == '__confirm__':
        return _handle_confirmation(sid, model)

    # Add user message to history
    session_manager.add_message(sid, 'user', question)

    # Choose dispatch mode
    if config.model_supports_tools(model):
        result = _native_tool_dispatch(question, sid, model)
    else:
        result = _keyword_tool_dispatch(question, sid, model)

    # Clean up and add assistant response to history
    if 'response' in result:
        result['response'] = _clean_response(result['response'])
        session_manager.add_message(sid, 'assistant', result['response'])

    result['session_id'] = sid
    return result


def _native_tool_dispatch(question, session_id, model):
    """Use Ollama's native tool calling (for capable models)."""
    # Build message history
    history = session_manager.get_messages(session_id, model)
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    messages.extend(history)

    # Add RAG context to the latest user message
    context = query_knowledge_base(question)
    if context:
        context_str = "\n\n".join(context)
        # Augment the last user message with context
        messages[-1] = {
            'role': 'user',
            'content': f"Context from CybICS documentation:\n{context_str}\n\nUser question: {question}"
        }

    tool_schemas = get_ollama_tool_schemas()

    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=tool_schemas,
        )
    except Exception as e:
        logger.error(f"Ollama native tool call error: {e}")
        # Fall back to keyword dispatch
        return _keyword_tool_dispatch(question, session_id, model)

    # Check if the model wants to call a tool
    if response.message.tool_calls:
        tools_used = []
        tool_results = []

        for tool_call in response.message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments or {}

            logger.info(f"Native tool call: {tool_name}({tool_args})")

            # Check for destructive action
            tool_info = AVAILABLE_TOOLS.get(tool_name, {})
            if tool_info.get('destructive'):
                session_manager.set_pending_action(session_id, tool_name, tool_args)
                desc = _describe_action(tool_name, tool_args)
                return {
                    'response': f"This action requires confirmation:\n\n**{desc}**\n\nAre you sure you want to proceed?",
                    'confirmation_required': True,
                    'pending_action': {'tool': tool_name, 'parameters': tool_args},
                    'sources': 0,
                }

            result = execute_tool(tool_name, tool_args)
            tools_used.append(tool_name)
            tool_results.append({
                'tool': tool_name,
                'parameters': tool_args,
                'result': result,
            })

        # Feed tool results back to the model for a natural language summary
        # Add assistant message with tool calls
        messages.append(response.message)

        # Add tool results as tool role messages
        for tr in tool_results:
            formatted = format_tool_result_for_llm(tr['tool'], tr['result'])
            messages.append({
                'role': 'tool',
                'content': formatted,
            })

        try:
            summary_response = ollama.chat(model=model, messages=messages)
            response_text = summary_response.message.content
        except Exception as e:
            logger.error(f"Error generating tool summary: {e}")
            # Fall back to formatted results
            response_text = "\n\n".join(
                format_tool_result_for_llm(tr['tool'], tr['result'])
                for tr in tool_results
            )

        return {
            'response': response_text,
            'sources': len(context),
            'tools_used': tools_used,
            'tool_results': tool_results,
        }

    # No tool call — just return the text response
    return {
        'response': response.message.content,
        'sources': len(context),
    }


def _keyword_tool_dispatch(question, session_id, model):
    """Keyword-based tool dispatch (fallback for small models)."""
    should_use_tool, tool_name, tool_params = detect_tool_intent(question)

    if should_use_tool:
        logger.info(f"Keyword dispatch: {tool_name}({tool_params})")

        # Check for destructive action
        tool_info = AVAILABLE_TOOLS.get(tool_name, {})
        if tool_info.get('destructive'):
            session_manager.set_pending_action(session_id, tool_name, tool_params)
            desc = _describe_action(tool_name, tool_params)
            return {
                'response': f"This action requires confirmation:\n\n**{desc}**\n\nAre you sure you want to proceed?",
                'confirmation_required': True,
                'pending_action': {'tool': tool_name, 'parameters': tool_params},
                'sources': 0,
            }

        result = execute_tool(tool_name, tool_params)
        formatted_result = format_tool_result_for_llm(tool_name, result)

        # Generate natural language response
        final_prompt = (
            f'The user asked: "{question}"\n\n'
            f'I executed the tool `{tool_name}` and got these results:\n\n'
            f'{formatted_result}\n\n'
            f'Provide a clear, helpful markdown response summarizing what was found. Be concise.'
        )

        try:
            final_response = ollama.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': final_prompt},
                ]
            )
            response_text = final_response.message.content
        except Exception as e:
            logger.error(f"Error generating tool summary: {e}")
            response_text = formatted_result

        return {
            'response': response_text,
            'sources': 0,
            'tools_used': [tool_name],
            'tool_results': [{'tool': tool_name, 'parameters': tool_params, 'result': result}],
        }

    # No tool — use RAG
    context = query_knowledge_base(question)
    response_text = _generate_rag_response(question, context, model)

    return {
        'response': response_text,
        'sources': len(context),
    }


def _generate_rag_response(question, context, model):
    """Generate a response using RAG context."""
    if not context:
        return (
            "I don't have specific information about that in my knowledge base. "
            "Here's what I can help you with:\n\n"
            "- **Training exercises**: Ask about scanning, Modbus, OPC-UA, password attacks, "
            "MITM, fuzzing, IDS, and more\n"
            "- **Live system tools**: Container status, network scans, Modbus registers, "
            "OPC-UA nodes, IDS alerts, process state\n"
            "- **CTF progress**: Ask \"what's my progress?\" or \"what should I do next?\"\n"
            "- **Defense challenges**: Ask me to verify your firewall, password, or IDS configurations\n\n"
            "Try asking something specific about the CybICS testbed or a training exercise!"
        )

    context_str = "\n\n".join(context)

    prompt = (
        f"Answer the question using ONLY the context below. "
        f"Do NOT make up information. If the context does not contain the answer, "
        f"say you don't have that information.\n\n"
        f"---\nContext:\n{context_str}\n---\n\n"
        f"Question: {question}\n\n"
        f"Answer (use markdown, be concise):"
    )

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': prompt},
            ]
        )
        return response.message.content
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "I'm having trouble connecting to the AI model. Please check the model configuration."


def _handle_confirmation(session_id, model):
    """Execute a previously confirmed destructive action."""
    action = session_manager.pop_pending_action(session_id)
    if not action:
        return {
            'response': 'No pending action to confirm.',
            'sources': 0,
        }

    tool_name = action['tool']
    parameters = action['parameters']

    logger.info(f"Executing confirmed action: {tool_name}({parameters})")
    result = execute_tool(tool_name, parameters)
    formatted = format_tool_result_for_llm(tool_name, result)

    try:
        summary = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user', 'content': f'I confirmed and executed `{tool_name}`. Results:\n\n{formatted}\n\nSummarize concisely.'},
            ]
        )
        response_text = summary.message.content
    except Exception:
        response_text = formatted

    return {
        'response': response_text,
        'sources': 0,
        'tools_used': [tool_name],
        'tool_results': [{'tool': tool_name, 'parameters': parameters, 'result': result}],
    }


def _clean_response(text):
    """Strip hallucinated links from model responses.

    Converts [text](url) markdown links to just the text, and removes
    bare URLs. This prevents broken/fake links in the chat UI.
    """
    # [text](url) → **text**
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'**\1**', text)
    # Bare URLs
    text = re.sub(r'https?://\S+', '', text)
    return text


def _describe_action(tool_name, parameters):
    """Generate a human-readable description of a tool action."""
    if tool_name == 'restart_containers':
        target = parameters.get('container_names')
        if target:
            return f"Restart container: {target}"
        return "Restart ALL containers"
    return f"Execute {tool_name}"


def detect_tool_intent(question):
    """
    Detect if the user's question requires tool execution based on keywords.
    Returns tuple: (should_use_tool, tool_name, parameters)
    """
    question_lower = question.lower()

    # --- ICS-specific tools (check before generic terms) ---

    # Modbus registers
    if any(word in question_lower for word in ['modbus', 'register', 'holding register', 'coil']):
        reg_type = 'holding'
        if 'input' in question_lower:
            reg_type = 'input'
        elif 'coil' in question_lower:
            reg_type = 'coil'
        elif 'discrete' in question_lower:
            reg_type = 'discrete'

        address = 0
        addr_match = re.search(r'address\s+(\d+)', question_lower)
        if addr_match:
            address = int(addr_match.group(1))

        count = 10
        count_match = re.search(r'(\d+)\s+register', question_lower)
        if count_match:
            count = int(count_match.group(1))

        return (True, 'read_modbus_registers', {
            'register_type': reg_type,
            'address': address,
            'count': count,
        })

    # OPC-UA
    if any(word in question_lower for word in ['opcua', 'opc-ua', 'opc ua']):
        action = 'browse'
        if 'read' in question_lower:
            action = 'read'

        node_id = None
        node_match = re.search(r'(ns=\d+;[si]=\d+)', question)
        if node_match:
            node_id = node_match.group(1)

        params = {'action': action}
        if node_id:
            params['node_id'] = node_id
        return (True, 'read_opcua_nodes', params)

    # IDS - forensics and summary (check before generic IDS alerts)
    if any(word in question_lower for word in ['forensic', 'investigation', 'incident']):
        return (True, 'get_ids_forensics_briefing', {})

    if any(word in question_lower for word in ['ids summary', 'alert summary', 'attacker', 'top source']):
        return (True, 'get_ids_summary', {})

    # IDS alerts (generic)
    if any(word in question_lower for word in ['ids', 'intrusion', 'alert', 'detection']):
        count = 20
        count_match = re.search(r'(\d+)\s+alert', question_lower)
        if count_match:
            count = int(count_match.group(1))
        return (True, 'check_ids_alerts', {'count': count})

    # --- Training & CTF tools ---

    # Process state / physical process monitoring
    if any(word in question_lower for word in [
        'pressure', 'tank', 'process state', 'compressor', 'valve',
        'blowout', 'gst', 'hpt', 'physical process', 'hwio',
    ]):
        return (True, 'get_process_state', {})

    # CTF progress
    if any(word in question_lower for word in [
        'progress', 'score', 'points', 'solved', 'ctf',
        'challenge', 'what should i do next', 'what next',
        'recommend', 'learning path',
    ]):
        return (True, 'get_ctf_progress', {})

    # Defense verification
    if any(word in question_lower for word in ['verify', 'check my']):
        # Try to identify which defense challenge
        defense_map = {
            'openplc': 'defense_openplc_password',
            'fuxa': 'defense_fuxa_password',
            'firewall': 'defense_firewall',
            'segmentation': 'defense_network_segmentation',
            'ids tuning': 'defense_ids_tuning',
            'ids monitoring': 'defense_ids_tuning',
        }
        for keyword, challenge_id in defense_map.items():
            if keyword in question_lower:
                return (True, 'verify_defense_challenge', {'challenge_id': challenge_id})

        # Generic "verify my defense" — try password first as most common
        if 'password' in question_lower:
            return (True, 'verify_defense_challenge', {'challenge_id': 'defense_openplc_password'})
        if 'defense' in question_lower or 'hardening' in question_lower:
            return (True, 'verify_defense_challenge', {'challenge_id': 'defense_openplc_password'})

    # Packet capture / network traffic analysis
    if any(word in question_lower for word in [
        'packet', 'capture', 'traffic', 'pcap', 'wireshark',
        'sniff', 'captured',
    ]):
        if 'stat' in question_lower:
            return (True, 'get_capture_stats', {})
        count = 50
        count_match = re.search(r'(\d+)\s+packet', question_lower)
        if count_match:
            count = int(count_match.group(1))
        return (True, 'get_network_packets', {'count': count})

    # --- Infrastructure tools ---

    # Container status
    if any(word in question_lower for word in ['status', 'running', 'list container', 'show container', 'which container']):
        return (True, 'get_container_status', {})

    # Restart containers (must specify which one)
    if 'restart' in question_lower:
        for container in config.CYBICS_CONTAINERS:
            if container in question_lower:
                return (True, 'restart_containers', {'container_names': container})
        # Don't allow restarting without a specific container name

    # System stats
    if any(word in question_lower for word in ['cpu', 'memory', 'resource', 'performance', 'usage']):
        return (True, 'get_system_stats', {})

    # Logs
    if 'log' in question_lower:
        for container in config.CYBICS_CONTAINERS:
            if container in question_lower:
                lines_match = re.search(r'(\d+)\s{0,5}lines?', question_lower[:200])
                lines = int(lines_match.group(1)) if lines_match else 50
                return (True, 'get_container_logs', {'container_name': container, 'lines': lines})
        return (False, None, {})

    # Network scan
    if any(word in question_lower for word in ['scan', 'nmap']):
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
