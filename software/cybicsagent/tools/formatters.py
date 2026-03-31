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
}
