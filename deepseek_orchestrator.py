#!/usr/bin/env python3
"""
DeepSeek Live System Orchestrator
A secure bridge between DeepSeek inference and live system execution.

Enhanced with Multi-Model Support and Hot-Swap Configuration.
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

# Import model interface
from model_interface import get_model

# Optional imports with graceful fallbacks
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. File monitoring disabled.")

class ExecutionMode(Enum):
    """Defines how commands should be executed"""
    AUTO_APPROVE = "auto_approve"
    PROMPT = "prompt"
    DRY_RUN = "dry_run"
    AUDIT_ONLY = "audit_only"

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

class CommandValidator:
    """Validates and sanitizes commands before execution"""
    def __init__(self, config: Dict):
        self.whitelist = set(config.get('whitelist', []))
        self.blacklist = set(config.get('blacklist', []))
        self.require_approval = set(config.get('require_approval_for', []))
    
    def validate(self, command: str) -> Tuple[bool, str]:
        if not command or not command.strip():
            return False, "Empty command"
        base_cmd = command.split()[0] if command.split() else ""
        for blocked in self.blacklist:
            if blocked in command:
                return False, f"Command contains blacklisted pattern: {blocked}"
        if self.whitelist and base_cmd not in self.whitelist:
            return False, f"Command '{base_cmd}' not in whitelist"
        dangerous_patterns = ['rm -rf /', 'dd if=', '> /dev/', 'chmod 777', 'curl | sh']
        for pattern in dangerous_patterns:
            if pattern in command:
                return False, f"Command contains dangerous pattern: {pattern}"
        return True, "Valid"
    
    def needs_approval(self, command: str) -> bool:
        base_cmd = command.split()[0] if command.split() else ""
        return base_cmd in self.require_approval

class CommandExecutor:
    """Executes validated commands with safety controls"""
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def execute(self, command: str, dry_run: bool = False) -> CommandResult:
        if dry_run:
            logging.info(f"[DRY RUN] Would execute: {command}")
            return CommandResult(True, f"[DRY RUN] {command}", "", 0, 0.0)
        
        start_time = time.time()
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=self.timeout)
            return CommandResult(result.returncode == 0, result.stdout, result.stderr, result.returncode, time.time() - start_time)
        except Exception as e:
            return CommandResult(False, "", str(e), -1, time.time() - start_time)

class DeepSeekOrchestrator:
    """Main orchestrator coordinating all components"""
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.load_config()
        self.setup_logging()
        self.audit_logger = AuditLogger(self.config.get('audit_log', 'deepseek_audit.db'))
        self.model = get_model(self.config)
        self.last_config_mtime = os.path.getmtime(self.config_path) if os.path.exists(self.config_path) else 0
        self.validator = CommandValidator(self.config.get('security', {}))
        self.executor = CommandExecutor(timeout=self.config.get('timeout', 30))
        self.execution_mode = ExecutionMode(self.config.get('execution_mode', 'prompt'))

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler('deepseek_orchestrator.log'), logging.StreamHandler()]
        )
        self.logger = logging.getLogger("orchestrator")

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                'model': {'type': 'mock'},
                'execution_mode': 'prompt',
                'timeout': 30,
                'security': {'whitelist': ['ls', 'cat', 'echo', 'pwd', 'date'], 'blacklist': ['rm -rf']},
                'audit_log': 'deepseek_audit.db'
            }

    def check_config_reload(self):
        """Hot-swap model if config changed"""
        try:
            if not os.path.exists(self.config_path): return
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self.last_config_mtime:
                self.logger.info("Config change detected, reloading model...")
                self.load_config()
                self.model = get_model(self.config)
                self.validator = CommandValidator(self.config.get('security', {}))
                self.execution_mode = ExecutionMode(self.config.get('execution_mode', 'prompt'))
                self.last_config_mtime = current_mtime
        except Exception as e:
            self.logger.error(f"Config reload failed: {e}")

    def process_request(self, trigger_source: str, user_input: str) -> Optional[CommandResult]:
        self.check_config_reload()
        self.logger.info(f"Processing request from {trigger_source}: {user_input}")
        
        deepseek_response = self.model.generate_suggestion(user_input)
        suggested_command = self.extract_command(deepseek_response)
        
        if not suggested_command:
            self.audit_logger.log_event('no_command_extracted', trigger_source=trigger_source, deepseek_input=user_input, deepseek_output=deepseek_response)
            return None
        
        is_valid, validation_reason = self.validator.validate(suggested_command)
        if not is_valid:
            self.audit_logger.log_event('validation_failed', trigger_source=trigger_source, suggested_command=suggested_command, execution_result=validation_reason)
            return None
        
        needs_approval = (self.execution_mode == ExecutionMode.PROMPT or self.validator.needs_approval(suggested_command))
        approved = self.get_user_approval(suggested_command, user_input) if needs_approval else True
        
        if not approved:
            self.audit_logger.log_event('user_rejected', trigger_source=trigger_source, suggested_command=suggested_command)
            return None
        
        result = self.executor.execute(suggested_command, dry_run=(self.execution_mode == ExecutionMode.DRY_RUN))
        self.audit_logger.log_event('command_executed', trigger_source=trigger_source, suggested_command=suggested_command, execution_result=json.dumps(result.__dict__))
        return result

    def extract_command(self, response: str) -> Optional[str]:
        response = response.strip()
        for prefix in ["I suggest running:", "Execute:", "Command:", "$", "#"]:
            if response.startswith(prefix): response = response[len(prefix):].strip()
        if response.startswith("```"):
            lines = response.split('\n')
            response = '\n'.join(lines[1:-1]) if len(lines) > 2 else ""
        return response.strip() if response.strip() else None

    def get_user_approval(self, command: str, context: str) -> bool:
        print(f"\nAPPROVAL REQUIRED: {command}\nContext: {context}")
        choice = input("Approve execution? [y/N]: ").lower()
        return choice == 'y'

    def run_cli_mode(self):
        print("DeepSeek Orchestrator CLI Mode (Ctrl+C to exit)")
        while True:
            try:
                user_input = input("\nAction: ")
                if user_input.lower() in ['exit', 'quit']: break
                self.process_request("cli", user_input)
            except KeyboardInterrupt: break

    def run_watch_mode(self, watch_dir="triggers"):
        if not WATCHDOG_AVAILABLE: return
        Path(watch_dir).mkdir(parents=True, exist_ok=True)
        class Handler(FileSystemEventHandler):
            def __init__(self, orchestrator): self.orchestrator = orchestrator
            def on_created(self, event):
                if not event.is_directory and event.src_path.endswith('.task'):
                    with open(event.src_path, 'r') as f: user_input = f.read().strip()
                    result = self.orchestrator.process_request("file_watch", user_input)
                    with open(event.src_path.replace('.task', '.result'), 'w') as f:
                        f.write(json.dumps(result.__dict__ if result else {"error": "Failed"}))
        
        observer = Observer()
        observer.schedule(Handler(self), watch_dir, recursive=False)
        observer.start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt: observer.stop()
        observer.join()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=['cli', 'watch'], default='cli')
    args = parser.parse_args()
    orchestrator = DeepSeekOrchestrator()
    if args.mode == 'cli': orchestrator.run_cli_mode()
    else: orchestrator.run_watch_mode()
