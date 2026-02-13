#!/usr/bin/env python3
"""
DeepSeek Orchestrator - Web API Server
Provides a REST API for remote command submission
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from functools import wraps

try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not installed. Install with: pip install flask")

from app_bridge import AppBridge

app = Flask(__name__)

# Load configuration
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

web_config = config.get('web_api', {})
API_KEY = web_config.get('api_key', 'your-secret-api-key-here')
REQUIRE_AUTH = web_config.get('require_auth', True)

# Initialize app bridge
bridge = AppBridge(triggers_dir=config.get('file_watch', {}).get('watch_dir', './triggers'))


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not REQUIRE_AUTH:
            return f(*args, **kwargs)
        
        # Check for API key in header
        provided_key = request.headers.get('X-API-Key')
        
        # Also check for API key in query parameter (less secure but convenient)
        if not provided_key:
            provided_key = request.args.get('api_key')
        
        if not provided_key or provided_key != API_KEY:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Valid API key required'
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'DeepSeek Orchestrator API'
    })


@app.route('/api/v1/execute', methods=['POST'])
@require_api_key
def execute_command():
    """
    Execute a command
    
    Request body:
    {
        "command": "Show disk space",
        "source": "web_api",
        "priority": "normal",
        "wait": false,
        "timeout": 30
    }
    """
    data = request.get_json()
    
    if not data or 'command' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Command is required'
        }), 400
    
    command = data['command']
    source = data.get('source', 'web_api')
    priority = data.get('priority', 'normal')
    wait = data.get('wait', False)
    timeout = data.get('timeout', 30)
    
    # Submit command
    task_file = bridge.submit_command(command, source=source, priority=priority)
    
    response = {
        'success': True,
        'task_file': task_file,
        'command': command,
        'timestamp': datetime.now().isoformat()
    }
    
    # Wait for result if requested
    if wait:
        result = bridge.wait_for_result(task_file, timeout=timeout)
        if result:
            response['result'] = result
        else:
            response['timeout'] = True
            response['message'] = 'Command submitted but result not available within timeout'
    
    return jsonify(response)


@app.route('/api/v1/batch', methods=['POST'])
@require_api_key
def execute_batch():
    """
    Execute multiple commands
    
    Request body:
    {
        "commands": ["command1", "command2", "command3"],
        "source": "web_api"
    }
    """
    data = request.get_json()
    
    if not data or 'commands' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'Commands array is required'
        }), 400
    
    commands = data['commands']
    source = data.get('source', 'web_api_batch')
    
    if not isinstance(commands, list):
        return jsonify({
            'error': 'Bad Request',
            'message': 'Commands must be an array'
        }), 400
    
    # Submit batch
    task_files = bridge.submit_batch(commands, source=source)
    
    return jsonify({
        'success': True,
        'count': len(task_files),
        'task_files': task_files,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/status', methods=['GET'])
@require_api_key
def get_status():
    """Get orchestrator queue status"""
    status = bridge.get_status()
    status['timestamp'] = datetime.now().isoformat()
    return jsonify(status)


@app.route('/api/v1/result/<path:task_id>', methods=['GET'])
@require_api_key
def get_result(task_id):
    """Get result for a specific task"""
    # Reconstruct task file path
    triggers_dir = Path(config.get('file_watch', {}).get('watch_dir', './triggers'))
    result_file = triggers_dir / f"{task_id}.result"
    
    if not result_file.exists():
        return jsonify({
            'error': 'Not Found',
            'message': 'Result not available yet or task does not exist'
        }), 404
    
    with open(result_file, 'r') as f:
        result_text = f.read()
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'result': result_text,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        'service': 'DeepSeek Orchestrator API',
        'version': '1.0',
        'authentication': 'API Key required in X-API-Key header or api_key query parameter' if REQUIRE_AUTH else 'None',
        'endpoints': [
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check',
                'auth_required': False
            },
            {
                'path': '/api/v1/execute',
                'method': 'POST',
                'description': 'Execute a single command',
                'auth_required': REQUIRE_AUTH,
                'body': {
                    'command': 'string (required)',
                    'source': 'string (optional, default: web_api)',
                    'priority': 'string (optional, default: normal)',
                    'wait': 'boolean (optional, default: false)',
                    'timeout': 'integer (optional, default: 30)'
                }
            },
            {
                'path': '/api/v1/batch',
                'method': 'POST',
                'description': 'Execute multiple commands',
                'auth_required': REQUIRE_AUTH,
                'body': {
                    'commands': 'array of strings (required)',
                    'source': 'string (optional, default: web_api_batch)'
                }
            },
            {
                'path': '/api/v1/status',
                'method': 'GET',
                'description': 'Get orchestrator queue status',
                'auth_required': REQUIRE_AUTH
            },
            {
                'path': '/api/v1/result/<task_id>',
                'method': 'GET',
                'description': 'Get result for a specific task',
                'auth_required': REQUIRE_AUTH
            }
        ],
        'examples': {
            'execute': {
                'curl': f'curl -X POST http://localhost:5000/api/v1/execute -H "X-API-Key: {API_KEY}" -H "Content-Type: application/json" -d \'{{\"command\": \"Show disk space\"}}\'',
                'python': '''
import requests

response = requests.post(
    'http://localhost:5000/api/v1/execute',
    headers={'X-API-Key': 'your-api-key'},
    json={'command': 'Show disk space', 'wait': True}
)
print(response.json())
'''
            }
        }
    }
    
    return jsonify(docs)


def main():
    """Start the web API server"""
    if not FLASK_AVAILABLE:
        print("Error: Flask is required for the web API")
        print("Install with: pip install flask")
        return
    
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    
    print(f"Starting DeepSeek Orchestrator Web API")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Authentication: {'Enabled' if REQUIRE_AUTH else 'Disabled'}")
    if REQUIRE_AUTH:
        print(f"API Key: {API_KEY}")
    print(f"\nAPI Documentation: http://{host}:{port}/api/v1/docs")
    print("\nPress Ctrl+C to stop")
    
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()
