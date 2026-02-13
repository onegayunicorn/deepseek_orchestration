#!/usr/bin/env python3
"""
DeepSeek Live System Orchestrator
A secure bridge between DeepSeek inference and live system execution.

This script monitors file system events, processes requests through DeepSeek,
and executes approved commands in a controlled, auditable manner.
"""

import os
import sys
import json
import time
import logging
import subprocess
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Optional imports with graceful fallbacks
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. File monitoring disabled.")
    print("Install with: pip install watchdog")

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("Warning: llama-cpp-python not installed. Using mock inference.")
    print("Install with: pip install llama-cpp-python")


class ExecutionMode(Enum):
    """Defines how commands should be executed"""
    AUTO_APPROVE = "auto_approve"  # Execute whitelisted commands automatically
    PROMPT = "prompt"              # Ask user for approval
    DRY_RUN = "dry_run"           # Simulate without execution
    AUDIT_ONLY = "audit_only"     # Log only, no execution


@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    execution_time: float


class AuditLogger:
    """Handles audit logging to SQLite database"""
    
    def __init__(self, db_path: str = "deepseek_audit.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize audit database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                trigger_source TEXT,
                deepseek_input TEXT,
                deepseek_output TEXT,
                suggested_command TEXT,
                approved BOOLEAN,
                executed BOOLEAN,
                execution_result TEXT,
                user_feedback TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def log_event(self, event_type: str, **kwargs):
        """Log an event to the audit database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_log 
            (timestamp, event_type, trigger_source, deepseek_input, deepseek_output,
             suggested_command, approved, executed, execution_result, user_feedback)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            event_type,
            kwargs.get('trigger_source'),
            kwargs.get('deepseek_input'),
            kwargs.get('deepseek_output'),
            kwargs.get('suggested_command'),
            kwargs.get('approved'),
            kwargs.get('executed'),
            kwargs.get('execution_result'),
            kwargs.get('user_feedback')
        ))
        
        conn.commit()
        conn.close()


class DeepSeekInference:
    """Handles DeepSeek model inference"""
    
    def __init__(self, model_path: Optional[str] = None, context_size: int = 2048):
        self.model_path = model_path
        self.context_size = context_size
        self.model = None
        
        if LLAMA_CPP_AVAILABLE and model_path and os.path.exists(model_path):
            try:
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=context_size,
                    n_threads=4,
                    verbose=False
                )
                logging.info(f"Loaded DeepSeek model from {model_path}")
            except Exception as e:
                logging.error(f"Failed to load model: {e}")
                self.model = None
        else:
            logging.warning("Using mock inference mode")
    
    def infer(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Run inference on the model"""
        if self.model:
            try:
                response = self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["</command>", "\n\n"]
                )
                return response['choices'][0]['text'].strip()
            except Exception as e:
                logging.error(f"Inference error: {e}")
                return f"Error: {e}"
        else:
            # Mock response for testing
            return self._mock_inference(prompt)
    
    def _mock_inference(self, prompt: str) -> str:
        """Mock inference for testing without actual model"""
        if "deploy" in prompt.lower():
            return "I suggest running: docker compose up -d"
        elif "list" in prompt.lower() or "show" in prompt.lower():
            return "I suggest running: ls -la"
        elif "status" in prompt.lower():
            return "I suggest running: systemctl status"
        else:
            return "I suggest running: echo 'Command processed'"


class CommandValidator:
    """Validates and sanitizes commands before execution"""
    
    def __init__(self, config: Dict):
        self.whitelist = set(config.get('whitelist', []))
        self.blacklist = set(config.get('blacklist', []))
        self.require_approval = set(config.get('require_approval_for', []))
    
    def validate(self, command: str) -> Tuple[bool, str]:
        """
        Validate a command against security policies
        Returns: (is_valid, reason)
        """
        if not command or not command.strip():
            return False, "Empty command"
        
        # Extract base command
        base_cmd = command.split()[0] if command.split() else ""
        
        # Check blacklist
        for blocked in self.blacklist:
            if blocked in command:
                return False, f"Command contains blacklisted pattern: {blocked}"
        
        # Check whitelist (if defined)
        if self.whitelist:
            if base_cmd not in self.whitelist:
                return False, f"Command '{base_cmd}' not in whitelist"
        
        # Check for dangerous patterns
        dangerous_patterns = ['rm -rf /', 'dd if=', '> /dev/', 'chmod 777', 'curl | sh']
        for pattern in dangerous_patterns:
            if pattern in command:
                return False, f"Command contains dangerous pattern: {pattern}"
        
        return True, "Valid"
    
    def needs_approval(self, command: str) -> bool:
        """Check if command requires user approval"""
        base_cmd = command.split()[0] if command.split() else ""
        return base_cmd in self.require_approval


class CommandExecutor:
    """Executes validated commands with safety controls"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def execute(self, command: str, dry_run: bool = False) -> CommandResult:
        """Execute a command with timeout and capture output"""
        if dry_run:
            logging.info(f"[DRY RUN] Would execute: {command}")
            return CommandResult(
                success=True,
                stdout=f"[DRY RUN] {command}",
                stderr="",
                return_code=0,
                execution_time=0.0
            )
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                return_code=result.returncode,
                execution_time=execution_time
            )
        
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {self.timeout} seconds",
                return_code=-1,
                execution_time=self.timeout
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=time.time() - start_time
            )


class DeepSeekOrchestrator:
    """Main orchestrator coordinating all components"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.audit_logger = AuditLogger(self.config.get('audit_log', 'deepseek_audit.db'))
        self.inference = DeepSeekInference(
            model_path=self.config.get('model_path'),
            context_size=self.config.get('context_size', 2048)
        )
        self.validator = CommandValidator(self.config.get('security', {}))
        self.executor = CommandExecutor(timeout=self.config.get('timeout', 30))
        self.execution_mode = ExecutionMode(self.config.get('execution_mode', 'prompt'))
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('deepseek_orchestrator.log'),
                logging.StreamHandler()
            ]
        )
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                'model_path': None,
                'context_size': 2048,
                'execution_mode': 'prompt',
                'timeout': 30,
                'security': {
                    'whitelist': ['ls', 'cat', 'echo', 'pwd', 'date', 'whoami'],
                    'blacklist': ['rm -rf', 'dd', 'mkfs'],
                    'require_approval_for': ['docker', 'git', 'systemctl']
                },
                'audit_log': 'deepseek_audit.db'
            }
    
    def process_request(self, trigger_source: str, user_input: str) -> Optional[CommandResult]:
        """Process a request through the full pipeline"""
        logging.info(f"Processing request from {trigger_source}: {user_input}")
        
        # Build prompt for DeepSeek
        system_prompt = """You are a helpful AI assistant that suggests Linux commands to accomplish tasks.
Your response should contain ONLY the command to execute, nothing else.
Be concise and suggest safe, appropriate commands."""
        
        full_prompt = f"{system_prompt}\n\nUser request: {user_input}\n\nSuggested command:"
        
        # Get DeepSeek's suggestion
        deepseek_response = self.inference.infer(full_prompt)
        logging.info(f"DeepSeek suggested: {deepseek_response}")
        
        # Extract command from response
        suggested_command = self.extract_command(deepseek_response)
        
        if not suggested_command:
            logging.warning("No valid command extracted from DeepSeek response")
            self.audit_logger.log_event(
                'no_command_extracted',
                trigger_source=trigger_source,
                deepseek_input=user_input,
                deepseek_output=deepseek_response
            )
            return None
        
        # Validate command
        is_valid, validation_reason = self.validator.validate(suggested_command)
        
        if not is_valid:
            logging.warning(f"Command validation failed: {validation_reason}")
            self.audit_logger.log_event(
                'validation_failed',
                trigger_source=trigger_source,
                deepseek_input=user_input,
                deepseek_output=deepseek_response,
                suggested_command=suggested_command,
                approved=False,
                executed=False,
                execution_result=validation_reason
            )
            return None
        
        # Determine if approval is needed
        needs_approval = (
            self.execution_mode == ExecutionMode.PROMPT or
            self.validator.needs_approval(suggested_command)
        )
        
        approved = True
        if needs_approval:
            approved = self.get_user_approval(suggested_command, user_input)
        
        if not approved:
            logging.info("Command not approved by user")
            self.audit_logger.log_event(
                'user_rejected',
                trigger_source=trigger_source,
                deepseek_input=user_input,
                deepseek_output=deepseek_response,
                suggested_command=suggested_command,
                approved=False,
                executed=False
            )
            return None
        
        # Execute command
        dry_run = self.execution_mode == ExecutionMode.DRY_RUN
        audit_only = self.execution_mode == ExecutionMode.AUDIT_ONLY
        
        if audit_only:
            logging.info(f"[AUDIT ONLY] Would execute: {suggested_command}")
            self.audit_logger.log_event(
                'audit_only',
                trigger_source=trigger_source,
                deepseek_input=user_input,
                deepseek_output=deepseek_response,
                suggested_command=suggested_command,
                approved=True,
                executed=False
            )
            return None
        
        result = self.executor.execute(suggested_command, dry_run=dry_run)
        
        logging.info(f"Execution result: success={result.success}, return_code={result.return_code}")
        
        # Log to audit
        self.audit_logger.log_event(
            'command_executed',
            trigger_source=trigger_source,
            deepseek_input=user_input,
            deepseek_output=deepseek_response,
            suggested_command=suggested_command,
            approved=True,
            executed=True,
            execution_result=json.dumps({
                'success': result.success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.return_code,
                'execution_time': result.execution_time
            })
        )
        
        return result
    
    def extract_command(self, response: str) -> Optional[str]:
        """Extract executable command from DeepSeek response"""
        # Remove common prefixes
        response = response.strip()
        
        prefixes_to_remove = [
            "I suggest running:",
            "You should run:",
            "Try running:",
            "Execute:",
            "Command:",
            "Run:",
            "$",
            "#"
        ]
        
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # Remove markdown code blocks
        if response.startswith("```"):
            lines = response.split('\n')
            response = '\n'.join(lines[1:-1]) if len(lines) > 2 else ""
        
        return response.strip() if response.strip() else None
    
    def get_user_approval(self, command: str, context: str) -> bool:
        """Get user approval for command execution"""
        print("\n" + "="*60)
        print("APPROVAL REQUIRED")
        print("="*60)
        print(f"Context: {context}")
        print(f"Suggested command: {command}")
        print("="*60)
        
        while True:
            response = input("Approve execution? [y/n/v(view details)]: ").lower().strip()
            if response == 'y':
                return True
            elif response == 'n':
                return False
            elif response == 'v':
                print(f"\nCommand breakdown:")
                print(f"  Base command: {command.split()[0]}")
                print(f"  Full command: {command}")
                print()
            else:
                print("Please enter 'y', 'n', or 'v'")
    
    def run_cli_mode(self):
        """Run in interactive CLI mode"""
        print("DeepSeek Orchestrator - CLI Mode")
        print("Type 'exit' to quit, 'help' for commands")
        print()
        
        while True:
            try:
                user_input = input(">>> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.print_help()
                    continue
                
                result = self.process_request('cli', user_input)
                
                if result:
                    print(f"\n--- Output ---")
                    print(result.stdout)
                    if result.stderr:
                        print(f"--- Errors ---")
                        print(result.stderr)
                    print(f"--- Completed in {result.execution_time:.2f}s ---\n")
            
            except KeyboardInterrupt:
                print("\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                logging.error(f"Error in CLI mode: {e}")
    
    def print_help(self):
        """Print help information"""
        print("""
Available commands:
  - Type any request in natural language
  - 'exit' - Quit the orchestrator
  - 'help' - Show this help message

Examples:
  >>> List all files in current directory
  >>> Show system status
  >>> Check disk usage
        """)


class TriggerFileHandler(FileSystemEventHandler):
    """Handles file system events for trigger files"""
    
    def __init__(self, orchestrator: DeepSeekOrchestrator):
        self.orchestrator = orchestrator
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process .flag and .task files
        if file_path.suffix not in ['.flag', '.task']:
            return
        
        logging.info(f"Trigger file detected: {file_path}")
        
        try:
            # Read file content as the request
            with open(file_path, 'r') as f:
                request = f.read().strip()
            
            # Process the request
            result = self.orchestrator.process_request(f'file:{file_path.name}', request)
            
            # Write result back to a result file
            result_path = file_path.with_suffix('.result')
            with open(result_path, 'w') as f:
                if result:
                    f.write(f"Success: {result.success}\n")
                    f.write(f"Return code: {result.return_code}\n")
                    f.write(f"\n--- Output ---\n{result.stdout}\n")
                    if result.stderr:
                        f.write(f"\n--- Errors ---\n{result.stderr}\n")
                else:
                    f.write("Request was not executed (validation failed or rejected)\n")
            
            # Remove trigger file
            os.remove(file_path)
            
        except Exception as e:
            logging.error(f"Error processing trigger file: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='DeepSeek Live System Orchestrator')
    parser.add_argument('--config', default='config.json', help='Path to configuration file')
    parser.add_argument('--mode', choices=['cli', 'watch'], default='cli',
                       help='Execution mode: cli (interactive) or watch (file monitoring)')
    parser.add_argument('--watch-dir', default='./triggers',
                       help='Directory to watch for trigger files (watch mode only)')
    
    args = parser.parse_args()
    
    orchestrator = DeepSeekOrchestrator(config_path=args.config)
    
    if args.mode == 'cli':
        orchestrator.run_cli_mode()
    
    elif args.mode == 'watch':
        if not WATCHDOG_AVAILABLE:
            print("Error: watchdog library required for watch mode")
            print("Install with: pip install watchdog")
            sys.exit(1)
        
        watch_dir = Path(args.watch_dir)
        watch_dir.mkdir(exist_ok=True)
        
        print(f"Watching directory: {watch_dir.absolute()}")
        print("Create .flag or .task files to trigger actions")
        print("Press Ctrl+C to stop")
        
        event_handler = TriggerFileHandler(orchestrator)
        observer = Observer()
        observer.schedule(event_handler, str(watch_dir), recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\nStopping file watcher...")
        
        observer.join()


if __name__ == '__main__':
    main()
