# DeepSeek Orchestrator - Usage Examples

## Example 1: Interactive CLI Mode

Run the orchestrator in interactive mode:

```bash
python3 deepseek_orchestrator.py --mode cli
```

Then type natural language requests:

```
>>> List all files in the current directory
DeepSeek suggested: ls -la
Approve execution? [y/n/v(view details)]: y

--- Output ---
total 48
drwxr-xr-x  5 user user  4096 Feb 13 10:30 .
drwxr-xr-x 10 user user  4096 Feb 13 10:00 ..
-rw-r--r--  1 user user  1234 Feb 13 10:30 config.json
...
--- Completed in 0.12s ---

>>> Show me disk usage
DeepSeek suggested: df -h
Approve execution? [y/n/v(view details)]: y

--- Output ---
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   20G   28G  42% /
...
--- Completed in 0.08s ---
```

## Example 2: File Watcher Mode

Start the file watcher:

```bash
python3 deepseek_orchestrator.py --mode watch --watch-dir ./triggers
```

Create a trigger file:

```bash
echo "Show me the current processes" > triggers/check_processes.task
```

The orchestrator will:
1. Detect the new `.task` file
2. Read the content
3. Ask DeepSeek for a command suggestion
4. Request your approval (if needed)
5. Execute the command
6. Write results to `check_processes.result`
7. Delete the trigger file

## Example 3: Automated Deployment

Create a deployment trigger:

```bash
cat > triggers/deploy.flag << EOF
Deploy the application using docker compose
EOF
```

The orchestrator will:
- Suggest: `docker compose up -d`
- Request approval (docker is in require_approval_for list)
- Execute after approval
- Log the entire process to audit database

## Example 4: System Monitoring

Create a monitoring task:

```bash
cat > triggers/monitor.task << EOF
Check system memory usage and show top 5 processes by memory
EOF
```

Expected DeepSeek suggestion:
```bash
ps aux --sort=-%mem | head -n 6
```

## Example 5: File Organization

```bash
cat > triggers/organize.task << EOF
List all PDF files in the Downloads directory
EOF
```

Expected suggestion:
```bash
find ~/Downloads -name "*.pdf" -type f
```

## Example 6: Code Review Helper

```bash
cat > triggers/review.task << EOF
Show me the git diff for the last commit
EOF
```

Expected suggestion:
```bash
git diff HEAD~1
```

Since `git` is in the `require_approval_for` list, you'll be prompted before execution.

## Example 7: Dry Run Mode

Modify `config.json` to test without execution:

```json
{
  "execution_mode": "dry_run",
  ...
}
```

Now all commands will be simulated:

```
>>> Delete old log files
DeepSeek suggested: find /var/log -name "*.log" -mtime +30 -delete
[DRY RUN] Would execute: find /var/log -name "*.log" -mtime +30 -delete
```

## Example 8: Audit Only Mode

For pure logging without execution:

```json
{
  "execution_mode": "audit_only",
  ...
}
```

All suggestions will be logged to the database but never executed.

## Example 9: Auto-Approve Mode (Advanced)

For trusted environments with strict whitelisting:

```json
{
  "execution_mode": "auto_approve",
  "security": {
    "whitelist": ["ls", "cat", "echo", "pwd", "date"],
    "blacklist": ["rm", "dd", "mkfs"],
    "require_approval_for": []
  }
}
```

Only whitelisted commands will execute automatically.

## Example 10: Querying Audit Logs

Check the audit database:

```bash
sqlite3 deepseek_audit.db "SELECT timestamp, event_type, suggested_command, approved, executed FROM audit_log ORDER BY timestamp DESC LIMIT 10;"
```

Or use a Python script:

```python
import sqlite3
import json

conn = sqlite3.connect('deepseek_audit.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT timestamp, trigger_source, deepseek_input, suggested_command, approved, executed
    FROM audit_log 
    WHERE executed = 1
    ORDER BY timestamp DESC 
    LIMIT 5
""")

print("Recent Executed Commands:")
print("-" * 80)
for row in cursor.fetchall():
    print(f"Time: {row[0]}")
    print(f"Source: {row[1]}")
    print(f"Request: {row[2]}")
    print(f"Command: {row[3]}")
    print(f"Approved: {row[4]}, Executed: {row[5]}")
    print("-" * 80)

conn.close()
```

## Example 11: Custom System Prompt

Modify the `process_request` method to customize DeepSeek's behavior:

```python
system_prompt = """You are a DevOps AI assistant specializing in Docker and Kubernetes.
Suggest commands that follow best practices for container orchestration.
Always prefer docker compose over raw docker commands.
Your response should contain ONLY the command to execute."""
```

## Example 12: Chained Operations

Create a task that requires multiple steps:

```bash
cat > triggers/backup.task << EOF
Create a backup of all Python files in the current directory
EOF
```

DeepSeek might suggest:
```bash
tar -czf python_backup_$(date +%Y%m%d).tar.gz *.py
```

## Example 13: Integration with Cron

Add to crontab for scheduled monitoring:

```bash
# Check system status every hour
0 * * * * echo "Show system load and memory usage" > /path/to/triggers/hourly_check.task
```

## Example 14: Voice Integration (Advanced)

Combine with speech-to-text:

```bash
# Record voice command
termux-microphone-record -f voice_command.wav -l 5

# Convert to text (using manus-speech-to-text or similar)
manus-speech-to-text voice_command.wav > triggers/voice_command.task

# Orchestrator processes it automatically
```

## Example 15: Web Interface (Future Enhancement)

Start a simple web server:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)
orchestrator = DeepSeekOrchestrator()

@app.route('/execute', methods=['POST'])
def execute():
    user_request = request.json.get('request')
    result = orchestrator.process_request('web_api', user_request)
    
    if result:
        return jsonify({
            'success': result.success,
            'output': result.stdout,
            'error': result.stderr
        })
    else:
        return jsonify({'success': False, 'error': 'Request rejected or failed validation'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Then trigger via HTTP:

```bash
curl -X POST http://localhost:5000/execute \
  -H "Content-Type: application/json" \
  -d '{"request": "Show me current directory contents"}'
```
