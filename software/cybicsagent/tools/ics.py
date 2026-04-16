"""CybICS AI Agent - ICS-specific tools (Modbus, OPC-UA, IDS)"""
import asyncio
import logging
import os

import requests

from config import (OPENPLC_HOST, MODBUS_PORT, OPCUA_HOST, OPCUA_PORT,
                    IDS_HOST, IDS_PORT, HWIO_HOST, HWIO_PORT)

logger = logging.getLogger(__name__)

# OPC-UA browse configuration
OPCUA_MAX_CHILDREN = int(os.getenv('OPCUA_MAX_CHILDREN', '50'))


def read_modbus_registers(register_type='holding', address=0, count=10):
    """
    Read Modbus registers from the OpenPLC controller.

    Args:
        register_type: Type of register to read - 'holding', 'input', 'coil', or 'discrete'.
        address: Starting register address (default: 0).
        count: Number of registers to read (default: 10).
    """
    # Validate parameters
    address = int(address)
    count = int(count)
    if not 0 <= address <= 65535:
        return {'error': f'Invalid address {address}: must be 0-65535'}
    if not 1 <= count <= 125:
        return {'error': f'Invalid count {count}: must be 1-125'}
    if register_type not in ('holding', 'input', 'coil', 'discrete'):
        return {'error': f'Invalid register type: {register_type}'}

    try:
        from pymodbus.client import ModbusTcpClient

        client = ModbusTcpClient(OPENPLC_HOST, port=MODBUS_PORT, timeout=5)
        if not client.connect():
            return {'error': f'Could not connect to Modbus at {OPENPLC_HOST}:{MODBUS_PORT}'}

        try:
            if register_type == 'holding':
                result = client.read_holding_registers(address, count)
            elif register_type == 'input':
                result = client.read_input_registers(address, count)
            elif register_type == 'coil':
                result = client.read_coils(address, count)
            elif register_type == 'discrete':
                result = client.read_discrete_inputs(address, count)

            if result.isError():
                return {'error': f'Modbus read error: {result}'}

            if register_type in ('coil', 'discrete'):
                values = list(result.bits[:count])
            else:
                values = list(result.registers)

            return {
                'success': True,
                'host': f'{OPENPLC_HOST}:{MODBUS_PORT}',
                'register_type': register_type,
                'start_address': address,
                'count': count,
                'values': values
            }
        finally:
            client.close()

    except ImportError:
        return {'error': 'pymodbus not installed - Modbus tools unavailable'}
    except Exception as e:
        logger.error(f"Error reading Modbus registers: {e}")
        return {'error': f'Failed to read Modbus registers: {str(e)}'}


def read_opcua_nodes(node_id=None, action='browse'):
    """
    Browse or read OPC-UA nodes from the CybICS OPC-UA server.

    Args:
        node_id: OPC-UA node ID to browse or read (e.g., 'ns=2;i=2').
            Defaults to the Objects folder if not specified.
        action: 'browse' to list child nodes, or 'read' to read a node's value.
    """
    try:
        from asyncua import Client as OpcuaClient

        async def _opcua_operation():
            client = OpcuaClient(f'opc.tcp://{OPCUA_HOST}:{OPCUA_PORT}')
            try:
                await client.connect()

                if node_id:
                    node = client.get_node(node_id)
                else:
                    node = client.nodes.objects

                if action == 'browse':
                    children = await node.get_children()
                    total_children = len(children)
                    nodes = []
                    for child in children[:OPCUA_MAX_CHILDREN]:
                        browse_name = await child.read_browse_name()
                        node_class = await child.read_node_class()
                        entry = {
                            'node_id': child.nodeid.to_string(),
                            'browse_name': browse_name.to_string(),
                            'node_class': str(node_class),
                        }
                        # Try to read value for Variable nodes
                        if 'Variable' in str(node_class):
                            try:
                                value = await child.read_value()
                                entry['value'] = str(value)
                            except Exception:
                                entry['value'] = '<unreadable>'
                        nodes.append(entry)

                    result = {
                        'success': True,
                        'host': f'{OPCUA_HOST}:{OPCUA_PORT}',
                        'action': 'browse',
                        'parent_node': node_id or 'Objects',
                        'children': nodes,
                        'total_children': total_children,
                    }
                    if total_children > OPCUA_MAX_CHILDREN:
                        result['truncated'] = True
                        result['message'] = f'Showing {OPCUA_MAX_CHILDREN} of {total_children} children'
                    return result

                elif action == 'read':
                    if not node_id:
                        return {'error': 'node_id is required for read action'}
                    value = await node.read_value()
                    browse_name = await node.read_browse_name()
                    data_type = await node.read_data_type_as_variant_type()
                    return {
                        'success': True,
                        'host': f'{OPCUA_HOST}:{OPCUA_PORT}',
                        'action': 'read',
                        'node_id': node_id,
                        'browse_name': browse_name.to_string(),
                        'value': str(value),
                        'data_type': str(data_type)
                    }
                else:
                    return {'error': f'Unknown action: {action}'}

            finally:
                await client.disconnect()

        # Use asyncio.run() which handles loop creation/cleanup properly.
        # Falls back to manual loop management if already in an event loop.
        try:
            return asyncio.run(_opcua_operation())
        except RuntimeError:
            # "RuntimeError: This event loop is already running" - we're in a thread with a loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(_opcua_operation())
            finally:
                loop.close()
                asyncio.set_event_loop(None)

    except ImportError:
        return {'error': 'asyncua not installed - OPC-UA tools unavailable'}
    except Exception as e:
        logger.error(f"Error with OPC-UA operation: {e}")
        return {'error': f'Failed OPC-UA {action}: {str(e)}'}


def check_ids_alerts(count=20):
    """
    Check recent IDS alerts and status from the CybICS intrusion detection system.

    Args:
        count: Number of recent alerts to retrieve (default: 20).
    """
    ids_url = f'http://{IDS_HOST}:{IDS_PORT}'
    try:
        status_resp = requests.get(f'{ids_url}/api/status', timeout=5)
        status_resp.raise_for_status()
        status = status_resp.json()

        alerts_resp = requests.get(f'{ids_url}/api/alerts', timeout=5)
        alerts_resp.raise_for_status()
        alerts_data = alerts_resp.json()
        alerts = alerts_data.get('alerts', [])[-count:]

        return {
            'success': True,
            'ids_status': status,
            'recent_alerts': alerts,
            'total_alerts': alerts_data.get('total', len(alerts_data.get('alerts', [])))
        }
    except requests.ConnectionError:
        return {'error': f'Could not connect to IDS at {ids_url} - is it running?'}
    except requests.Timeout:
        return {'error': 'IDS request timed out'}
    except Exception as e:
        logger.error(f"Error checking IDS alerts: {e}")
        return {'error': f'Failed to check IDS: {str(e)}'}


def get_process_state():
    """
    Get the current physical process state from the HWIO virtual simulation.
    Returns real-time values for gas storage tank pressure, high pressure tank,
    compressor, valves, and sensor states.
    """
    hwio_url = f'http://{HWIO_HOST}:{HWIO_PORT}'
    try:
        resp = requests.get(f'{hwio_url}/api/state', timeout=5)
        resp.raise_for_status()
        state = resp.json()

        # Add human-readable interpretations
        gst = state.get('gst', 0)
        hpt = state.get('hpt', 0)
        bo_sen = state.get('boSen', 0)

        warnings = []
        if hpt > 200:
            warnings.append('CRITICAL: HPT pressure dangerously high - blowout imminent!')
        elif hpt > 150:
            warnings.append('WARNING: HPT pressure elevated')
        if bo_sen > 0:
            warnings.append('ALERT: Blowout sensor triggered!')

        return {
            'success': True,
            'host': f'{HWIO_HOST}:{HWIO_PORT}',
            'process_state': {
                'gas_storage_tank_pressure': gst,
                'high_pressure_tank_pressure': hpt,
                'system_sensor': state.get('sysSen', 0),
                'blowout_sensor': bo_sen,
                'compressor': 'ON' if state.get('compressor', 0) else 'OFF',
                'system_valve': 'OPEN' if state.get('systemValve', 0) else 'CLOSED',
                'gst_signal': state.get('gstSig', 0),
                'heartbeat': state.get('heartbeat', 0),
            },
            'warnings': warnings,
        }
    except requests.ConnectionError:
        return {'error': f'Could not connect to HWIO at {hwio_url} - is it running?'}
    except requests.Timeout:
        return {'error': 'HWIO request timed out'}
    except Exception as e:
        logger.error(f"Error getting process state: {e}")
        return {'error': f'Failed to get process state: {str(e)}'}


def get_ids_summary():
    """
    Get IDS alert summary statistics for forensic analysis.
    Returns severity breakdown, top attackers, rule statistics, and timeline data.
    """
    ids_url = f'http://{IDS_HOST}:{IDS_PORT}'
    try:
        summary_resp = requests.get(f'{ids_url}/api/summary', timeout=5)
        summary_resp.raise_for_status()
        summary = summary_resp.json()

        rules_resp = requests.get(f'{ids_url}/api/rules/stats', timeout=5)
        rules_resp.raise_for_status()
        rules = rules_resp.json()

        return {
            'success': True,
            'summary': summary,
            'rule_stats': rules,
        }
    except requests.ConnectionError:
        return {'error': f'Could not connect to IDS at {ids_url} - is it running?'}
    except Exception as e:
        logger.error(f"Error getting IDS summary: {e}")
        return {'error': f'Failed to get IDS summary: {str(e)}'}


def get_ids_forensics_briefing():
    """
    Get the IDS forensics challenge briefing with investigation questions.
    Use this to guide students through incident analysis.
    """
    ids_url = f'http://{IDS_HOST}:{IDS_PORT}'
    try:
        resp = requests.get(f'{ids_url}/api/forensics', timeout=5)
        resp.raise_for_status()
        return {
            'success': True,
            'forensics': resp.json(),
        }
    except requests.ConnectionError:
        return {'error': f'Could not connect to IDS at {ids_url}'}
    except Exception as e:
        logger.error(f"Error getting forensics briefing: {e}")
        return {'error': f'Failed to get forensics briefing: {str(e)}'}
