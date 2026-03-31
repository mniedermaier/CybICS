"""CybICS AI Agent - Tool registry and execution"""
import logging

from tools.containers import get_container_status, restart_containers, get_container_logs
from tools.system import get_system_stats, list_docker_images
from tools.network import execute_network_scan
from tools.ics import read_modbus_registers, read_opcua_nodes, check_ids_alerts

logger = logging.getLogger(__name__)

# Tool definitions with JSON Schema-compatible parameter types
AVAILABLE_TOOLS = {
    'get_container_status': {
        'function': get_container_status,
        'description': 'Get the status of all running Docker containers in CybICS',
        'parameters': {},
        'destructive': False,
    },
    'restart_containers': {
        'function': restart_containers,
        'description': 'Restart one or more Docker containers. Can restart all containers or specific ones.',
        'parameters': {
            'container_names': {
                'type': 'string',
                'description': 'Name of container to restart (e.g. "openplc", "fuxa"). Leave empty to restart all.',
                'required': False,
            }
        },
        'destructive': True,
    },
    'get_container_logs': {
        'function': get_container_logs,
        'description': 'Get recent logs from a specific Docker container',
        'parameters': {
            'container_name': {
                'type': 'string',
                'description': 'Name of the container to get logs from (e.g. "openplc", "fuxa", "landing")',
                'required': True,
            },
            'lines': {
                'type': 'integer',
                'description': 'Number of log lines to retrieve (default: 50)',
                'required': False,
            }
        },
        'destructive': False,
    },
    'get_system_stats': {
        'function': get_system_stats,
        'description': 'Get real-time resource usage statistics for all containers (CPU, memory, network)',
        'parameters': {},
        'destructive': False,
    },
    'execute_network_scan': {
        'function': execute_network_scan,
        'description': 'Execute a network scan using nmap on the CybICS network',
        'parameters': {
            'target': {
                'type': 'string',
                'description': 'Target IP address or network range (e.g., "172.18.0.0/24")',
                'required': True,
            },
            'scan_type': {
                'type': 'string',
                'description': 'Type of scan: "basic" (ping), "port" (all ports), "service" (version detection), "vuln" (vulnerability scan)',
                'required': False,
            }
        },
        'destructive': False,
    },
    'list_docker_images': {
        'function': list_docker_images,
        'description': 'List all Docker images available on the system',
        'parameters': {},
        'destructive': False,
    },
    'read_modbus_registers': {
        'function': read_modbus_registers,
        'description': 'Read Modbus registers from the OpenPLC controller to inspect process values',
        'parameters': {
            'register_type': {
                'type': 'string',
                'description': 'Type of register: "holding", "input", "coil", or "discrete" (default: "holding")',
                'required': False,
            },
            'address': {
                'type': 'integer',
                'description': 'Starting register address (default: 0)',
                'required': False,
            },
            'count': {
                'type': 'integer',
                'description': 'Number of registers to read (default: 10)',
                'required': False,
            }
        },
        'destructive': False,
    },
    'read_opcua_nodes': {
        'function': read_opcua_nodes,
        'description': 'Browse or read OPC-UA nodes from the CybICS OPC-UA server',
        'parameters': {
            'node_id': {
                'type': 'string',
                'description': 'OPC-UA node ID to browse or read (e.g. "ns=2;i=2"). Defaults to Objects folder.',
                'required': False,
            },
            'action': {
                'type': 'string',
                'description': '"browse" to list child nodes, "read" to read a node value (default: "browse")',
                'required': False,
            }
        },
        'destructive': False,
    },
    'check_ids_alerts': {
        'function': check_ids_alerts,
        'description': 'Check recent IDS alerts and intrusion detection status',
        'parameters': {
            'count': {
                'type': 'integer',
                'description': 'Number of recent alerts to retrieve (default: 20)',
                'required': False,
            }
        },
        'destructive': False,
    },
}


def execute_tool(tool_name, parameters=None):
    """Execute a tool function with given parameters."""
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
        logger.error(f"Invalid parameters for {tool_name}: {e}")
        return {'error': f'Invalid parameters for {tool_name}'}
    except Exception as e:
        logger.error(f"Error executing {tool_name}: {e}")
        return {'error': f'Error executing {tool_name}'}


def get_ollama_tool_schemas():
    """Convert AVAILABLE_TOOLS to Ollama-native tool call format."""
    schemas = []
    for name, tool_info in AVAILABLE_TOOLS.items():
        properties = {}
        required = []
        for param_name, param_info in tool_info['parameters'].items():
            prop = {
                'type': param_info['type'],
                'description': param_info['description'],
            }
            properties[param_name] = prop
            if param_info.get('required'):
                required.append(param_name)

        schemas.append({
            'type': 'function',
            'function': {
                'name': name,
                'description': tool_info['description'],
                'parameters': {
                    'type': 'object',
                    'properties': properties,
                    'required': required,
                }
            }
        })
    return schemas
