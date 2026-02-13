#!/usr/bin/env python3
"""
DeepSeek Orchestrator - AlienPC Ω Mesh Integration
Bridges the orchestrator with the P2P mesh network and council governance
"""

import os
import json
import time
import requests
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# Configuration
CONFIG_PATH = Path("config.json")
MESH_CONFIG_PATH = Path("../alienpc-mesh/alienpc-mesh/mesh_config.yml")
COUNCIL_CLI = Path("../alienpc-mesh/alienpc-mesh/council/governance/council-cli.py")

class AlienPCIntegration:
    """Integration bridge for AlienPC Ω Mesh and Council"""
    
    def __init__(self):
        self.load_config()
        self.mesh_url = f"http://localhost:{self.config.get('mesh_port', 8080)}"
        self.api_key = self.config.get('web_api', {}).get('api_key')
        self.running = False

    def load_config(self):
        """Load orchestrator configuration"""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {}

    def broadcast_event(self, event_type, data):
        """Broadcast an event to the mesh network"""
        payload = {
            'id': f"evt-{int(time.time())}-{os.urandom(4).hex()}",
            'type': event_type,
            'source': f"deepseek-node-{os.uname().nodename}",
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        try:
            # Send to local mesh agent
            response = requests.post(
                f"{self.mesh_url}/broadcast",
                json=payload,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to broadcast to mesh: {e}")
            return False

    def sync_proposals(self):
        """Sync council proposals and trigger actions if approved"""
        try:
            # Call council-cli to list approved proposals
            result = subprocess.run(
                ['python3', str(COUNCIL_CLI), 'list', '--status', 'approved'],
                capture_output=True, text=True, check=True
            )
            
            # Parse output (assuming it prints JSON or structured text)
            # For now, we'll look for specific categories like 'system_command'
            # in the proposals directory
            proposals_dir = COUNCIL_CLI.parent / "proposals"
            if not proposals_dir.exists():
                return
                
            for prop_file in proposals_dir.glob("*.yml"):
                import yaml
                with open(prop_file) as f:
                    prop = yaml.safe_load(f)
                    
                if prop.get('status') == 'approved' and prop.get('category') == 'system_command':
                    # Check if already processed
                    processed_flag = prop_file.with_suffix('.processed')
                    if not processed_flag.exists():
                        print(f"Processing approved proposal: {prop['id']}")
                        self.execute_proposal_command(prop)
                        processed_flag.touch()
                        
        except Exception as e:
            print(f"Failed to sync proposals: {e}")

    def execute_proposal_command(self, prop):
        """Execute a command from an approved proposal"""
        command = prop.get('description') # Or a specific field
        if not command:
            return
            
        print(f"Executing council-approved command: {command}")
        
        # Submit to orchestrator via file trigger
        trigger_dir = Path(self.config.get('file_watch', {}).get('watch_dir', './triggers'))
        trigger_dir.mkdir(parents=True, exist_ok=True)
        
        task_id = f"council-{prop['id']}"
        with open(trigger_dir / f"{task_id}.task", 'w') as f:
            f.write(command)

    def start_sync_loop(self):
        """Start background sync loop"""
        self.running = True
        def loop():
            while self.running:
                self.sync_proposals()
                # Heartbeat to mesh
                self.broadcast_event('heartbeat', {
                    'status': 'active',
                    'load': os.getloadavg()
                })
                time.sleep(60)
                
        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    integration = AlienPCIntegration()
    print("Starting AlienPC Ω Integration Bridge...")
    integration.start_sync_loop()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        integration.stop()
        print("Integration stopped.")
