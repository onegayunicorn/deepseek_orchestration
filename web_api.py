#!/usr/bin/env python3
"""
DeepSeek Orchestrator - Enhanced Web API Server
Production-grade REST API with rate limiting, dashboard integration, and advanced monitoring
"""

import os
import json
import time
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from functools import wraps
from collections import defaultdict

try:
    from flask import Flask, request, jsonify, render_template_string
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask or Flask-Limiter not installed. Install with: pip install flask flask-limiter")

from app_bridge import AppBridge

app = Flask(__name__)

# Load configuration
CONFIG_PATH = "config.json"
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

web_config = config.get('web_api', {})
API_KEY = web_config.get('api_key', 'your-secret-api-key-here')
REQUIRE_AUTH = web_config.get('require_auth', True)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "20 per minute"],
    storage_uri="memory://"
)

# Initialize app bridge
bridge = AppBridge(triggers_dir=config.get('file_watch', {}).get('watch_dir', './triggers'))

# Webhook storage
WEBHOOKS_FILE = "webhooks.json"
webhooks = []

def load_webhooks():
    """Load registered webhooks"""
    global webhooks
    if os.path.exists(WEBHOOKS_FILE):
        with open(WEBHOOKS_FILE, 'r') as f:
            webhooks = json.load(f)

def save_webhooks():
    """Save registered webhooks"""
    with open(WEBHOOKS_FILE, 'w') as f:
        json.dump(webhooks, f, indent=2)

load_webhooks()


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


def get_system_health():
    """Get comprehensive system health"""
    health_data = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {},
        'system': {}
    }
    
    # Check tmux session
    try:
        result = subprocess.run(['tmux', 'has-session', '-t', 'deepseek'], 
                              capture_output=True, timeout=5)
        health_data['services']['tmux_session'] = 'running' if result.returncode == 0 else 'stopped'
    except:
        health_data['services']['tmux_session'] = 'unknown'
    
    # Check orchestrator log
    log_file = Path('deepseek_orchestrator.log')
    if log_file.exists():
        log_age = time.time() - log_file.stat().st_mtime
        health_data['services']['orchestrator'] = 'active' if log_age < 300 else 'idle'
        health_data['services']['orchestrator_log_age_seconds'] = int(log_age)
    else:
        health_data['services']['orchestrator'] = 'not_started'
    
    # Check audit database
    db_file = Path('deepseek_audit.db')
    if db_file.exists():
        health_data['services']['audit_database'] = 'available'
        health_data['services']['audit_db_size_bytes'] = db_file.stat().st_size
    else:
        health_data['services']['audit_database'] = 'not_created'
    
    # System metrics
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
            health_data['system']['uptime_seconds'] = int(uptime_seconds)
    except:
        pass
    
    try:
        with open('/proc/loadavg', 'r') as f:
            load = f.read().split()
            health_data['system']['load_average'] = {
                '1min': float(load[0]),
                '5min': float(load[1]),
                '15min': float(load[2])
            }
    except:
        pass
    
    return health_data


def get_audit_records(limit=100, status=None):
    """Get audit records from database"""
    db_file = Path('deepseek_audit.db')
    if not db_file.exists():
        return []
    
    try:
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM audit_log 
                WHERE status = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
        
        records = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return records
    except Exception as e:
        print(f"Error reading audit database: {e}")
        return []


def get_metrics():
    """Get system metrics"""
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'queue': {},
        'audit': {},
        'system': {}
    }
    
    # Queue metrics
    status = bridge.get_status()
    metrics['queue'] = status
    
    # Audit metrics
    db_file = Path('deepseek_audit.db')
    if db_file.exists():
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM audit_log")
            metrics['audit']['total_commands'] = cursor.fetchone()[0]
            
            # Status breakdown
            cursor.execute("SELECT status, COUNT(*) FROM audit_log GROUP BY status")
            metrics['audit']['by_status'] = dict(cursor.fetchall())
            
            # Recent activity (last hour)
            cursor.execute("""
                SELECT COUNT(*) FROM audit_log 
                WHERE datetime(timestamp) > datetime('now', '-1 hour')
            """)
            metrics['audit']['last_hour'] = cursor.fetchone()[0]
            
            # Top sources
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM audit_log 
                GROUP BY source 
                ORDER BY count DESC 
                LIMIT 5
            """)
            metrics['audit']['top_sources'] = dict(cursor.fetchall())
            
            conn.close()
        except Exception as e:
            metrics['audit']['error'] = str(e)
    
    # System metrics
    try:
        result = subprocess.run(['df', '-h', '.'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                metrics['system']['disk'] = {
                    'total': parts[1],
                    'used': parts[2],
                    'available': parts[3],
                    'use_percent': parts[4]
                }
    except:
        pass
    
    return metrics


@app.route('/health', methods=['GET'])
@limiter.exempt
def health():
    """Health check endpoint (no rate limit)"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'DeepSeek Orchestrator API'
    })


@app.route('/api/v1/execute', methods=['POST'])
@require_api_key
@limiter.limit("10 per minute")
def execute_command():
    """Execute a command with rate limiting"""
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
    
    # Trigger webhooks
    for webhook in webhooks:
        try:
            import requests
            requests.post(webhook['url'], json={
                'event': 'command_executed',
                'command': command,
                'task_file': task_file,
                'timestamp': response['timestamp']
            }, timeout=5)
        except:
            pass
    
    return jsonify(response)


@app.route('/api/v1/batch', methods=['POST'])
@require_api_key
@limiter.limit("5 per minute")
def execute_batch():
    """Execute multiple commands"""
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
    """Get comprehensive system status"""
    health_data = get_system_health()
    queue_status = bridge.get_status()
    
    return jsonify({
        **health_data,
        'queue': queue_status
    })


@app.route('/api/v1/metrics', methods=['GET'])
@require_api_key
def api_metrics():
    """Get system metrics"""
    return jsonify(get_metrics())


@app.route('/api/v1/audit', methods=['GET'])
@require_api_key
def get_audit():
    """Get audit log records"""
    limit = request.args.get('limit', 100, type=int)
    status = request.args.get('status', None)
    
    if limit > 1000:
        limit = 1000
    
    records = get_audit_records(limit=limit, status=status)
    
    return jsonify({
        'success': True,
        'count': len(records),
        'records': records,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/watchdog', methods=['GET'])
@require_api_key
def watchdog_status():
    """Get watchdog and tmux pane status"""
    status = {
        'timestamp': datetime.now().isoformat(),
        'tmux_session': 'unknown',
        'windows': []
    }
    
    try:
        # Check if session exists
        result = subprocess.run(['tmux', 'has-session', '-t', 'deepseek'], 
                              capture_output=True, timeout=5)
        status['tmux_session'] = 'running' if result.returncode == 0 else 'stopped'
        
        if result.returncode == 0:
            # List windows
            result = subprocess.run(['tmux', 'list-windows', '-t', 'deepseek', '-F', 
                                   '#{window_index}:#{window_name}:#{pane_current_command}'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        parts = line.split(':')
                        if len(parts) >= 3:
                            status['windows'].append({
                                'index': parts[0],
                                'name': parts[1],
                                'command': parts[2]
                            })
    except Exception as e:
        status['error'] = str(e)
    
    return jsonify(status)


@app.route('/api/v1/webhook/register', methods=['POST'])
@require_api_key
def register_webhook():
    """Register a webhook URL"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({
            'error': 'Bad Request',
            'message': 'URL is required'
        }), 400
    
    webhook = {
        'url': data['url'],
        'name': data.get('name', 'Unnamed'),
        'registered_at': datetime.now().isoformat()
    }
    
    webhooks.append(webhook)
    save_webhooks()
    
    return jsonify({
        'success': True,
        'webhook': webhook,
        'total_webhooks': len(webhooks)
    })


@app.route('/api/v1/webhook/list', methods=['GET'])
@require_api_key
def list_webhooks():
    """List registered webhooks"""
    return jsonify({
        'success': True,
        'count': len(webhooks),
        'webhooks': webhooks
    })


@app.route('/api/v1/webhook/delete/<int:index>', methods=['DELETE'])
@require_api_key
def delete_webhook(index):
    """Delete a webhook by index"""
    if 0 <= index < len(webhooks):
        removed = webhooks.pop(index)
        save_webhooks()
        return jsonify({
            'success': True,
            'removed': removed,
            'remaining': len(webhooks)
        })
    else:
        return jsonify({
            'error': 'Not Found',
            'message': 'Webhook index not found'
        }), 404


@app.route('/api/v1/result/<path:task_id>', methods=['GET'])
@require_api_key
def get_result(task_id):
    """Get result for a specific task"""
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


@app.route('/dashboard', methods=['GET'])
@require_api_key
def dashboard():
    """Simple HTML dashboard"""
    health = get_system_health()
    metrics = get_metrics()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DeepSeek Orchestrator Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #0a0e27;
                color: #e0e0e0;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #4c9aff;
                border-bottom: 2px solid #4c9aff;
                padding-bottom: 10px;
            }
            h2 {
                color: #6dd5ed;
                margin-top: 30px;
            }
            .card {
                background: #1a1f3a;
                border-radius: 8px;
                padding: 20px;
                margin: 15px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }
            .status-healthy {
                color: #00ff88;
                font-weight: bold;
            }
            .status-warning {
                color: #ffaa00;
                font-weight: bold;
            }
            .status-error {
                color: #ff4444;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #2a2f4a;
            }
            th {
                background: #2a2f4a;
                color: #6dd5ed;
            }
            .metric {
                display: inline-block;
                margin: 10px 20px 10px 0;
            }
            .metric-label {
                color: #888;
                font-size: 0.9em;
            }
            .metric-value {
                color: #4c9aff;
                font-size: 1.5em;
                font-weight: bold;
            }
            .refresh-btn {
                background: #4c9aff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
            }
            .refresh-btn:hover {
                background: #6dd5ed;
            }
        </style>
        <script>
            function refreshDashboard() {
                location.reload();
            }
            setTimeout(refreshDashboard, 30000); // Auto-refresh every 30 seconds
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🦅 DeepSeek Orchestrator Dashboard</h1>
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
            
            <div class="card">
                <h2>System Status</h2>
                <p>Status: <span class="status-healthy">{{ health.status }}</span></p>
                <p>Timestamp: {{ health.timestamp }}</p>
                
                <h3>Services</h3>
                <table>
                    <tr>
                        <th>Service</th>
                        <th>Status</th>
                    </tr>
                    {% for service, status in health.services.items() %}
                    <tr>
                        <td>{{ service }}</td>
                        <td>{{ status }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            
            <div class="card">
                <h2>Metrics</h2>
                <div class="metric">
                    <div class="metric-label">Total Commands</div>
                    <div class="metric-value">{{ metrics.audit.get('total_commands', 0) }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Last Hour</div>
                    <div class="metric-value">{{ metrics.audit.get('last_hour', 0) }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Queue Pending</div>
                    <div class="metric-value">{{ metrics.queue.get('pending', 0) }}</div>
                </div>
            </div>
            
            {% if metrics.audit.get('by_status') %}
            <div class="card">
                <h2>Command Status Breakdown</h2>
                <table>
                    <tr>
                        <th>Status</th>
                        <th>Count</th>
                    </tr>
                    {% for status, count in metrics.audit.by_status.items() %}
                    <tr>
                        <td>{{ status }}</td>
                        <td>{{ count }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            {% endif %}
            
            {% if metrics.system.get('disk') %}
            <div class="card">
                <h2>Disk Usage</h2>
                <p>Total: {{ metrics.system.disk.total }}</p>
                <p>Used: {{ metrics.system.disk.used }} ({{ metrics.system.disk.use_percent }})</p>
                <p>Available: {{ metrics.system.disk.available }}</p>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    
    from jinja2 import Template
    template = Template(html)
    return template.render(health=health, metrics=metrics)


@app.route('/api/v1/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    docs = {
        'service': 'DeepSeek Orchestrator API',
        'version': '2.0',
        'authentication': 'API Key required in X-API-Key header or api_key query parameter' if REQUIRE_AUTH else 'None',
        'rate_limits': {
            'default': '100 per hour, 20 per minute',
            'execute': '10 per minute',
            'batch': '5 per minute'
        },
        'endpoints': [
            {
                'path': '/health',
                'method': 'GET',
                'description': 'Health check (no auth, no rate limit)',
                'auth_required': False
            },
            {
                'path': '/api/v1/execute',
                'method': 'POST',
                'description': 'Execute a single command',
                'auth_required': REQUIRE_AUTH,
                'rate_limit': '10 per minute'
            },
            {
                'path': '/api/v1/batch',
                'method': 'POST',
                'description': 'Execute multiple commands',
                'auth_required': REQUIRE_AUTH,
                'rate_limit': '5 per minute'
            },
            {
                'path': '/api/v1/status',
                'method': 'GET',
                'description': 'Get comprehensive system status',
                'auth_required': REQUIRE_AUTH
            },
            {
                'path': '/api/v1/metrics',
                'method': 'GET',
                'description': 'Get system metrics and statistics',
                'auth_required': REQUIRE_AUTH
            },
            {
                'path': '/api/v1/audit',
                'method': 'GET',
                'description': 'Get audit log records',
                'auth_required': REQUIRE_AUTH,
                'params': {
                    'limit': 'integer (max 1000)',
                    'status': 'string (filter by status)'
                }
            },
            {
                'path': '/api/v1/watchdog',
                'method': 'GET',
                'description': 'Get tmux session and window status',
                'auth_required': REQUIRE_AUTH
            },
            {
                'path': '/api/v1/webhook/register',
                'method': 'POST',
                'description': 'Register a webhook URL',
                'auth_required': REQUIRE_AUTH
            },
            {
                'path': '/api/v1/webhook/list',
                'method': 'GET',
                'description': 'List registered webhooks',
                'auth_required': REQUIRE_AUTH
            },
            {
                'path': '/dashboard',
                'method': 'GET',
                'description': 'HTML dashboard',
                'auth_required': REQUIRE_AUTH
            }
        ]
    }
    
    return jsonify(docs)


def main():
    """Start the enhanced web API server"""
    if not FLASK_AVAILABLE:
        print("Error: Flask and Flask-Limiter are required")
        print("Install with: pip install flask flask-limiter")
        return
    
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    
    print(f"Starting DeepSeek Orchestrator Enhanced Web API")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Authentication: {'Enabled' if REQUIRE_AUTH else 'Disabled'}")
    if REQUIRE_AUTH:
        print(f"API Key: {API_KEY}")
    print(f"\nEndpoints:")
    print(f"  API Documentation: http://{host}:{port}/api/v1/docs")
    print(f"  Dashboard: http://{host}:{port}/dashboard")
    print(f"  Health: http://{host}:{port}/health")
    print(f"\nRate Limiting: Enabled")
    print(f"  Default: 100/hour, 20/minute")
    print(f"  Execute: 10/minute")
    print(f"  Batch: 5/minute")
    print("\nPress Ctrl+C to stop")
    
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()
