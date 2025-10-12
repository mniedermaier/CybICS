#!/usr/bin/env python3
"""
Lightweight HTTP service that provides host network statistics.
Runs on host network mode to access real host network interfaces.
"""
from flask import Flask, jsonify
import psutil
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/network/stats')
def network_stats():
    """Get network stats excluding Docker-related interfaces"""
    try:
        net_io_per_nic = psutil.net_io_counters(pernic=True)

        bytes_recv = 0
        bytes_sent = 0

        for interface, stats in net_io_per_nic.items():
            # Skip loopback and docker interfaces
            if interface.startswith(('lo', 'docker', 'br-', 'veth')):
                continue

            bytes_recv += stats.bytes_recv
            bytes_sent += stats.bytes_sent

        return jsonify({
            'bytes_recv': bytes_recv,
            'bytes_sent': bytes_sent,
            'source': 'host'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090, debug=False)
