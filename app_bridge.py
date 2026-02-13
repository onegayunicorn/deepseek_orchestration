#!/usr/bin/env python3
"""
DeepSeek Orchestrator - App Bridge
Provides a simple API for external apps to submit commands to the orchestrator
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

class AppBridge:
    """Bridge for external applications to communicate with the orchestrator"""
    
    def __init__(self, triggers_dir="./triggers"):
        self.triggers_dir = Path(triggers_dir)
        self.triggers_dir.mkdir(parents=True, exist_ok=True)
    
    def submit_command(self, command: str, source: str = "app", priority: str = "normal") -> str:
        """
        Submit a command to the orchestrator
        
        Args:
            command: The natural language command to execute
            source: Identifier for the calling application
            priority: Priority level (low, normal, high)
        
        Returns:
            Path to the created task file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        task_file = self.triggers_dir / f"{source}_{priority}_{timestamp}.task"
        
        # Write command to task file
        with open(task_file, 'w') as f:
            f.write(command)
        
        return str(task_file)
    
    def submit_batch(self, commands: list, source: str = "app") -> list:
        """
        Submit multiple commands at once
        
        Args:
            commands: List of command strings
            source: Identifier for the calling application
        
        Returns:
            List of created task file paths
        """
        task_files = []
        for i, cmd in enumerate(commands):
            task_file = self.submit_command(cmd, source=f"{source}_batch{i}")
            task_files.append(task_file)
            time.sleep(0.1)  # Small delay to ensure unique timestamps
        
        return task_files
    
    def wait_for_result(self, task_file: str, timeout: int = 30) -> dict:
        """
        Wait for the orchestrator to process a task and return the result
        
        Args:
            task_file: Path to the task file
            timeout: Maximum seconds to wait
        
        Returns:
            Dictionary with result data or None if timeout
        """
        task_path = Path(task_file)
        result_path = task_path.with_suffix('.result')
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if result_path.exists():
                with open(result_path, 'r') as f:
                    result_text = f.read()
                
                # Parse result
                return {
                    'success': 'Success: True' in result_text or 'Return code: 0' in result_text,
                    'output': result_text,
                    'result_file': str(result_path)
                }
            
            time.sleep(0.5)
        
        return None  # Timeout
    
    def get_status(self) -> dict:
        """Get current status of the orchestrator queue"""
        pending_tasks = list(self.triggers_dir.glob("*.task"))
        completed_results = list(self.triggers_dir.glob("*.result"))
        
        return {
            'pending_tasks': len(pending_tasks),
            'completed_results': len(completed_results),
            'task_files': [str(f) for f in pending_tasks],
            'result_files': [str(f) for f in completed_results]
        }


def main():
    """CLI interface for the app bridge"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek Orchestrator App Bridge')
    parser.add_argument('command', nargs='?', help='Command to submit')
    parser.add_argument('--source', default='cli', help='Source identifier')
    parser.add_argument('--priority', default='normal', choices=['low', 'normal', 'high'],
                       help='Priority level')
    parser.add_argument('--wait', action='store_true', help='Wait for result')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for waiting')
    parser.add_argument('--status', action='store_true', help='Show queue status')
    parser.add_argument('--batch', action='store_true', help='Read commands from stdin (one per line)')
    
    args = parser.parse_args()
    
    bridge = AppBridge()
    
    if args.status:
        status = bridge.get_status()
        print(json.dumps(status, indent=2))
        return
    
    if args.batch:
        commands = [line.strip() for line in sys.stdin if line.strip()]
        print(f"Submitting {len(commands)} commands...")
        task_files = bridge.submit_batch(commands, source=args.source)
        print(f"Created {len(task_files)} task files")
        for tf in task_files:
            print(f"  - {tf}")
        return
    
    if not args.command:
        parser.print_help()
        return
    
    # Submit single command
    task_file = bridge.submit_command(args.command, source=args.source, priority=args.priority)
    print(f"Task submitted: {task_file}")
    
    if args.wait:
        print(f"Waiting for result (timeout: {args.timeout}s)...")
        result = bridge.wait_for_result(task_file, timeout=args.timeout)
        
        if result:
            print("\n=== Result ===")
            print(result['output'])
            sys.exit(0 if result['success'] else 1)
        else:
            print("Timeout: No result received")
            sys.exit(2)


if __name__ == '__main__':
    main()
