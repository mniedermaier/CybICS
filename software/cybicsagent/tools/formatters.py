"""CybICS AI Agent - Tool result formatters for LLM consumption"""
import json


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
    """Format tool results in a readable way for the LLM to process."""
    if 'error' in result:
        return f"**Error**: {result['error']}"

    formatter = _FORMATTERS.get(tool_name)
    if formatter:
        formatted = formatter(result)
        if formatted:
            return formatted

    return f"```json\n{json.dumps(result, indent=2)}\n```"


def _format_container_status(result):
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


def _format_system_stats(result):
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


def _format_restart_containers(result):
    if result.get('success'):
        restarted = result.get('restarted', [])
        formatted = f"**Successfully restarted {len(restarted)} container(s)**\n\n"
        for c in restarted:
            formatted += f"- `{c}`\n"
        return formatted
    else:
        failed = result.get('failed', [])
        succeeded = result.get('restarted', [])
        formatted = f"**Partial success**: {len(succeeded)} restarted, {len(failed)} failed\n\n"
        if succeeded:
            formatted += "**Restarted**:\n"
            for c in succeeded:
                formatted += f"- `{c}`\n"
        if failed:
            formatted += "\n**Failed**:\n"
            for c in failed:
                formatted += f"- `{c}`\n"
        return formatted


def _format_container_logs(result):
    if result.get('success'):
        container = result.get('container', 'unknown')
        logs = result.get('logs', '')
        if len(logs) > 2000:
            logs = logs[-2000:] + "\n... (truncated)"
        return f"**Logs from** `{container}`\n\n```\n{logs}\n```"


def _format_docker_images(result):
    if result.get('success') and 'images' in result:
        images = result['images']
        formatted = f"**Docker Images** ({len(images)} total)\n\n"
        formatted += "| Repository | Tag | Size |\n"
        formatted += "|------------|-----|------|\n"
        for img in images[:20]:
            repo = img.get('Repository', 'unknown')
            tag = img.get('Tag', 'unknown')
            size = img.get('Size', 'unknown')
            formatted += f"| `{repo}` | `{tag}` | {size} |\n"
        if len(images) > 20:
            formatted += f"\n... and {len(images) - 20} more"
        return formatted


def _format_network_scan(result):
    if result.get('success'):
        scan_type = result.get('scan_type', 'unknown')
        target = result.get('target', 'unknown')
        results = result.get('results', '')
        if len(results) > 1500:
            results = results[:1500] + "\n... (truncated)"
        formatted = f"**Network Scan Results**\n\n"
        formatted += f"- **Type**: {scan_type}\n"
        formatted += f"- **Target**: `{target}`\n\n"
        formatted += f"```\n{results}\n```"
        return formatted


def _format_modbus_registers(result):
    if result.get('success'):
        formatted = f"**Modbus Registers** from `{result['host']}`\n\n"
        formatted += f"- **Type**: {result['register_type']}\n"
        formatted += f"- **Start address**: {result['start_address']}\n\n"
        formatted += "| Address | Value |\n"
        formatted += "|---------|-------|\n"
        for i, val in enumerate(result['values']):
            formatted += f"| {result['start_address'] + i} | `{val}` |\n"
        return formatted


def _format_opcua_nodes(result):
    if result.get('success') and result.get('action') == 'browse':
        children = result.get('children', [])
        formatted = f"**OPC-UA Nodes** under `{result.get('parent_node', 'Objects')}`\n\n"
        formatted += "| Node ID | Name | Class | Value |\n"
        formatted += "|---------|------|-------|-------|\n"
        for node in children:
            nid = node.get('node_id', '')
            name = node.get('browse_name', '')
            cls = node.get('node_class', '')
            val = node.get('value', '')
            formatted += f"| `{nid}` | {name} | {cls} | {val} |\n"
        return formatted
    elif result.get('success') and result.get('action') == 'read':
        formatted = f"**OPC-UA Node Value**\n\n"
        formatted += f"- **Node**: `{result.get('node_id')}`\n"
        formatted += f"- **Name**: {result.get('browse_name')}\n"
        formatted += f"- **Value**: `{result.get('value')}`\n"
        formatted += f"- **Type**: {result.get('data_type')}\n"
        return formatted


def _format_ids_alerts(result):
    if result.get('success'):
        status = result.get('ids_status', {})
        alerts = result.get('recent_alerts', [])
        total = result.get('total_alerts', 0)

        formatted = f"**IDS Status**: {status.get('status', 'unknown')}\n"
        formatted += f"- **Total alerts**: {total}\n\n"

        if alerts:
            formatted += f"**Recent Alerts** (showing {len(alerts)}):\n\n"
            formatted += "| Time | Rule | Source | Destination |\n"
            formatted += "|------|------|--------|-------------|\n"
            for alert in alerts[-20:]:  # limit table rows
                time = alert.get('timestamp', alert.get('time', ''))
                rule = alert.get('rule', alert.get('msg', 'unknown'))
                src = alert.get('src', alert.get('source', ''))
                dst = alert.get('dst', alert.get('destination', ''))
                formatted += f"| {time} | {rule} | `{src}` | `{dst}` |\n"
        else:
            formatted += "No recent alerts detected.\n"
        return formatted


def _format_process_state(result):
    if result.get('success'):
        state = result.get('process_state', {})
        warnings = result.get('warnings', [])
        formatted = "**Physical Process State**\n\n"
        formatted += "| Parameter | Value |\n"
        formatted += "|-----------|-------|\n"
        formatted += f"| Gas Storage Tank (GST) | `{state.get('gas_storage_tank_pressure', 0)}` bar |\n"
        formatted += f"| High Pressure Tank (HPT) | `{state.get('high_pressure_tank_pressure', 0)}` bar |\n"
        formatted += f"| Compressor | {state.get('compressor', 'OFF')} |\n"
        formatted += f"| System Valve | {state.get('system_valve', 'CLOSED')} |\n"
        formatted += f"| System Sensor | `{state.get('system_sensor', 0)}` |\n"
        formatted += f"| Blowout Sensor | `{state.get('blowout_sensor', 0)}` |\n"
        formatted += f"| Heartbeat | `{state.get('heartbeat', 0)}` |\n"
        if warnings:
            formatted += "\n**Warnings:**\n"
            for w in warnings:
                formatted += f"- {w}\n"
        return formatted


def _format_ids_summary(result):
    if result.get('success'):
        summary = result.get('summary', {})
        rules = result.get('rule_stats', {})

        formatted = "**IDS Alert Summary**\n\n"

        # Severity breakdown
        severity = summary.get('severity', {})
        if severity:
            formatted += "**By Severity:**\n"
            for level, count in severity.items():
                formatted += f"- {level}: {count}\n"
            formatted += "\n"

        # Top sources
        top_sources = summary.get('top_sources', [])
        if top_sources:
            formatted += "**Top Attackers:**\n"
            for src in top_sources[:5]:
                ip = src.get('ip', src) if isinstance(src, dict) else src
                cnt = src.get('count', '') if isinstance(src, dict) else ''
                formatted += f"- `{ip}` ({cnt} alerts)\n" if cnt else f"- `{ip}`\n"
            formatted += "\n"

        # Rule stats
        rule_list = rules.get('rules', [])
        if rule_list:
            formatted += "**Rule Statistics:**\n\n"
            formatted += "| Rule | Hits | Last Seen |\n"
            formatted += "|------|------|-----------|\n"
            for rule in rule_list:
                name = rule.get('name', rule.get('rule', 'unknown'))
                hits = rule.get('hits', rule.get('count', 0))
                last = rule.get('last_seen', '')
                formatted += f"| {name} | {hits} | {last} |\n"

        return formatted


def _format_ids_forensics(result):
    if result.get('success'):
        forensics = result.get('forensics', {})
        formatted = "**IDS Forensics Briefing**\n\n"
        formatted += f"{forensics.get('scenario', '')}\n\n"

        questions = forensics.get('questions', [])
        if questions:
            formatted += "**Investigation Questions:**\n\n"
            for i, q in enumerate(questions, 1):
                if isinstance(q, dict):
                    formatted += f"{i}. {q.get('question', q.get('text', str(q)))}\n"
                else:
                    formatted += f"{i}. {q}\n"
            formatted += "\n"

        hint = forensics.get('hint', '')
        if hint:
            formatted += f"**Hint:** {hint}\n"
        return formatted


def _format_ctf_progress(result):
    if result.get('success'):
        progress = result.get('progress', {})
        formatted = "**CTF Progress**\n\n"
        formatted += f"- **Solved**: {progress.get('solved', 0)} / {progress.get('total', 0)} challenges\n"
        formatted += f"- **Points**: {progress.get('total_points', 0)} / {progress.get('max_points', 0)}\n\n"

        categories = progress.get('categories', {})
        if categories:
            formatted += "**By Category:**\n\n"
            formatted += "| Category | Solved | Total |\n"
            formatted += "|----------|--------|-------|\n"
            for cat_name, cat_data in categories.items():
                if isinstance(cat_data, dict):
                    solved = cat_data.get('solved', 0)
                    total = cat_data.get('total', 0)
                    name = cat_data.get('name', cat_name)
                    formatted += f"| {name} | {solved} | {total} |\n"

        unsolved = progress.get('unsolved', [])
        if unsolved:
            formatted += "\n**Next Challenges:**\n"
            for ch in unsolved[:5]:
                if isinstance(ch, dict):
                    formatted += f"- {ch.get('title', ch.get('id', ''))} ({ch.get('points', '')} pts)\n"

        return formatted


def _format_verify_defense(result):
    if result.get('success'):
        verification = result.get('verification', {})
        challenge_id = result.get('challenge_id', '')
        passed = verification.get('passed', verification.get('success', False))

        if passed:
            formatted = f"**Defense Challenge Verified: `{challenge_id}`**\n\n"
            formatted += "Result: PASSED\n"
            msg = verification.get('message', '')
            if msg:
                formatted += f"\n{msg}\n"
        else:
            formatted = f"**Defense Challenge: `{challenge_id}`**\n\n"
            formatted += "Result: NOT YET PASSED\n"
            msg = verification.get('message', verification.get('error', ''))
            if msg:
                formatted += f"\n{msg}\n"
            details = verification.get('details', '')
            if details:
                formatted += f"\n**Details:** {details}\n"
        return formatted


def _format_network_packets(result):
    if result.get('success'):
        packets = result.get('packets', [])
        protocols = result.get('protocol_summary', {})
        total = result.get('total_packets', 0)
        active = result.get('capture_active', False)

        formatted = f"**Network Capture** ({'Active' if active else 'Inactive'})\n\n"
        formatted += f"**Packets:** {total}\n\n"

        if protocols:
            formatted += "**Protocol Breakdown:**\n"
            for proto, count in sorted(protocols.items(), key=lambda x: -x[1]):
                formatted += f"- {proto}: {count}\n"
            formatted += "\n"

        if packets:
            formatted += "**Recent Packets:**\n\n"
            formatted += "| # | Protocol | Source | Destination | Info |\n"
            formatted += "|---|----------|--------|-------------|------|\n"
            for i, pkt in enumerate(packets[-20:], 1):
                proto = pkt.get('protocol', '?')
                src = pkt.get('src', pkt.get('source', ''))
                dst = pkt.get('dst', pkt.get('destination', ''))
                info = pkt.get('info', pkt.get('summary', ''))[:60]
                formatted += f"| {i} | {proto} | `{src}` | `{dst}` | {info} |\n"
        else:
            formatted += "No packets captured. Start a capture first.\n"
        return formatted


def _format_capture_stats(result):
    if result.get('success'):
        stats = result.get('stats', {})
        formatted = "**Capture Statistics**\n\n"
        for key, value in stats.items():
            formatted += f"- **{key}**: {value}\n"
        return formatted


# Formatter dispatch table
_FORMATTERS = {
    'get_container_status': _format_container_status,
    'get_system_stats': _format_system_stats,
    'restart_containers': _format_restart_containers,
    'get_container_logs': _format_container_logs,
    'list_docker_images': _format_docker_images,
    'execute_network_scan': _format_network_scan,
    'read_modbus_registers': _format_modbus_registers,
    'read_opcua_nodes': _format_opcua_nodes,
    'check_ids_alerts': _format_ids_alerts,
    'get_process_state': _format_process_state,
    'get_ids_summary': _format_ids_summary,
    'get_ids_forensics_briefing': _format_ids_forensics,
    'get_ctf_progress': _format_ctf_progress,
    'verify_defense_challenge': _format_verify_defense,
    'get_network_packets': _format_network_packets,
    'get_capture_stats': _format_capture_stats,
}
