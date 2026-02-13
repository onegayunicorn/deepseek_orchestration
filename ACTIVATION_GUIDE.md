# DeepSeek Orchestrator - Complete Activation Guide

This guide will walk you through activating your sovereign AI orchestration system from start to finish.

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone the Repository

```bash
cd ~
gh repo clone onegayunicorn/deepseek_orchestration
cd deepseek_orchestration
```

### Step 2: Run Setup

```bash
bash setup_termux.sh
```

This installs all dependencies. When prompted about `llama-cpp-python`, choose:
- **Yes** if you have a GGUF model and want real AI inference
- **No** if you want to test in mock mode first

### Step 3: Launch the Orchestrator

```bash
bash launch.sh
```

Select option **1** (CLI Mode) to start interacting immediately.

---

## 📋 Complete Setup Process

### Prerequisites

1. **Termux** installed from F-Droid (NOT Google Play)
2. **Termux:API** app installed from F-Droid (for voice features)
3. At least **2GB free storage** (4-8GB if using a full model)

### Installation Steps

#### 1. Storage Access

Grant Termux access to your device storage:

```bash
termux-setup-storage
```

Accept the Android permission prompt.

#### 2. Update Termux

```bash
pkg update && pkg upgrade
```

#### 3. Clone Repository

```bash
cd ~
gh repo clone onegayunicorn/deepseek_orchestration
cd deepseek_orchestration
```

#### 4. Run Setup Script

```bash
bash setup_termux.sh
```

The script will:
- Install Python, pip, git, and essential tools
- Install Python dependencies (watchdog, etc.)
- Optionally compile llama-cpp-python (takes 10-30 minutes)
- Create directory structure
- Generate default configuration

#### 5. Configure (Optional)

Edit `config.json` to customize:

```bash
nano config.json
```

Key settings:
- `model_path`: Path to your GGUF model file (or `null` for mock mode)
- `execution_mode`: `"prompt"` (safest), `"auto_approve"`, `"dry_run"`, or `"audit_only"`
- `whitelist`: Commands that are always allowed
- `blacklist`: Commands that are always blocked
- `require_approval_for`: Commands that need user confirmation

---

## 🎯 Activation Modes

### Mode 1: CLI (Interactive)

**Best for:** Direct interaction, testing, learning

```bash
bash launch.sh cli
```

**Usage:**
```
>>> Show disk space
DeepSeek suggested: df -h
Approve execution? [y/n]: y
```

---

### Mode 2: File Watcher

**Best for:** Automation, app integration, scheduled tasks

```bash
bash launch.sh watch
```

**Usage:**

In another terminal:
```bash
echo "List all Python files" > triggers/find_python.task
```

The orchestrator automatically processes it and creates `find_python.result`.

---

### Mode 3: Voice Command

**Best for:** Hands-free operation, accessibility

**Requirements:** Termux:API installed

```bash
bash launch.sh voice
```

**Usage:**
1. Script starts recording for 5 seconds
2. Say: "**Orchestrator** show disk space"
3. Command is transcribed and queued
4. Orchestrator processes it

---

### Mode 4: Continuous Voice Listener

**Best for:** Always-on voice assistant

```bash
bash launch.sh voice-listener
```

Continuously listens for voice commands with automatic cooldown.

---

### Mode 5: Web API

**Best for:** Remote control, web apps, external integrations

```bash
bash launch.sh web
```

**Access:** `http://localhost:5000`

**Example:**
```bash
curl -X POST http://localhost:5000/api/v1/execute \
  -H "X-API-Key: your-secret-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"command": "Show disk space", "wait": true}'
```

---

### Mode 6: System Monitor

**Best for:** Health monitoring, performance tracking

```bash
bash launch.sh monitor
```

Real-time dashboard showing:
- Queue status
- Execution statistics
- Success rates
- Recent activity

---

### Mode 7: All Services (tmux)

**Best for:** Production deployment

```bash
bash launch.sh all
```

Starts in tmux:
- **Window 0:** Orchestrator (watch mode)
- **Window 1:** Web API
- **Window 2:** Monitor

**tmux Commands:**
- Detach: `Ctrl+B` then `D`
- Switch windows: `Ctrl+B` then `0`, `1`, or `2`
- Reattach: `tmux attach -t deepseek_orchestrator`

---

### Mode 8: Full Stack (tmux)

**Best for:** Complete sovereign AI system

```bash
bash launch.sh full
```

Starts in tmux:
- **Window 0:** Orchestrator (watch mode)
- **Window 1:** Web API
- **Window 2:** Voice Listener
- **Window 3:** Monitor

---

## 🔧 Advanced Configuration

### Adding a Real Model

1. Download a GGUF model (e.g., from HuggingFace)
2. Place it in `~/models/` or any directory
3. Update `config.json`:

```json
{
  "model_path": "/data/data/com.termux/files/home/models/deepseek-coder-6.7b.Q4_K_M.gguf",
  ...
}
```

4. Restart the orchestrator

### Security Hardening

**Whitelist-Only Mode:**

```json
{
  "execution_mode": "prompt",
  "security": {
    "whitelist": ["ls", "cat", "echo", "pwd", "df", "du"],
    "blacklist": ["rm", "dd", "mkfs", "chmod 777"],
    "require_approval_for": []
  }
}
```

**Voice Security:**

```json
{
  "voice": {
    "enabled": true,
    "require_approval_for_all": true,
    "wake_word": "orchestrator",
    "rate_limit_seconds": 5
  }
}
```

### Web API Security

**Enable Authentication:**

```json
{
  "web_api": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 5000,
    "require_auth": true,
    "api_key": "generate-a-strong-random-key-here"
  }
}
```

**Generate API Key:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🔍 Using the Tools

### App Bridge

Submit commands from Python scripts:

```python
from app_bridge import AppBridge

bridge = AppBridge()
task_file = bridge.submit_command("Show system uptime", source="my_app")
result = bridge.wait_for_result(task_file, timeout=30)
print(result['output'])
```

### Audit Query

**Recent commands:**
```bash
python3 audit_query.py recent --limit 20
```

**Executed commands:**
```bash
python3 audit_query.py executed --limit 10
```

**Search:**
```bash
python3 audit_query.py search "docker"
```

**Statistics:**
```bash
python3 audit_query.py stats
```

### Monitor

**One-time status:**
```bash
python3 monitor.py
```

**Continuous monitoring:**
```bash
python3 monitor.py --watch --interval 5
```

**JSON output:**
```bash
python3 monitor.py --json
```

---

## 🔄 Integration Examples

### Cron/Scheduled Tasks

```bash
# Add to crontab
crontab -e

# Check system status every hour
0 * * * * echo "Show system load and memory" > ~/deepseek_orchestration/triggers/hourly_check.task
```

### Tasker/Automate Integration

Create a Tasker task that writes to the triggers directory:

```bash
echo "Take a backup" > /storage/emulated/0/deepseek_orchestration/triggers/backup.task
```

### Termux Widget

Create a shortcut script in `~/.shortcuts/`:

```bash
mkdir -p ~/.shortcuts
cat > ~/.shortcuts/orchestrator-status.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/deepseek_orchestration
python3 monitor.py
read -p "Press Enter to close"
EOF
chmod +x ~/.shortcuts/orchestrator-status.sh
```

---

## 🐛 Troubleshooting

### "Command not found" errors

**Solution:** Re-run setup script
```bash
bash setup_termux.sh
```

### Model loading fails

**Solution 1:** Check model path in `config.json`
**Solution 2:** Set `model_path` to `null` for mock mode

### Voice commands not working

**Solution 1:** Install Termux:API from F-Droid
**Solution 2:** Grant microphone permissions to Termux
**Solution 3:** Test with: `termux-microphone-record -d 3 -f test.wav`

### Permission denied errors

**Solution:** Termux doesn't use `sudo`. Remove from whitelist.

### Commands not executing

**Solution:** Check `execution_mode` in config. Change to `"prompt"` if set to `"audit_only"` or `"dry_run"`.

### Web API connection refused

**Solution 1:** Check if API is running: `ps aux | grep web_api`
**Solution 2:** Verify port in config matches your request
**Solution 3:** Use `127.0.0.1` instead of `localhost`

---

## 📊 Monitoring & Maintenance

### Daily Health Check

```bash
bash launch.sh status
```

### Weekly Audit Review

```bash
python3 audit_query.py stats
python3 audit_query.py rejected --limit 50
```

### Clean Old Results

```bash
# Remove result files older than 7 days
find triggers/ -name "*.result" -mtime +7 -delete
```

### Backup Audit Database

```bash
cp deepseek_audit.db deepseek_audit_backup_$(date +%Y%m%d).db
```

---

## 🎓 Next Steps

1. **Test in Mock Mode:** Get familiar with the system without a model
2. **Add a Real Model:** Download and configure a GGUF model
3. **Customize Security:** Adjust whitelist/blacklist for your needs
4. **Enable Voice:** Set up Termux:API for hands-free operation
5. **Integrate Apps:** Use app_bridge.py to connect your scripts
6. **Deploy Full Stack:** Run all services with tmux
7. **Monitor Performance:** Use the monitor tool regularly
8. **Review Audit Logs:** Check what your AI agent is doing

---

## 🆘 Support

- **Documentation:** See README.md, examples.md, architecture.md
- **Audit Logs:** `sqlite3 deepseek_audit.db "SELECT * FROM audit_log LIMIT 10;"`
- **GitHub Issues:** Report bugs or request features
- **Community:** Share your use cases and configurations

---

## ✅ Activation Checklist

- [ ] Termux installed from F-Droid
- [ ] Termux:API installed (for voice features)
- [ ] Repository cloned
- [ ] Setup script completed
- [ ] Configuration reviewed
- [ ] CLI mode tested
- [ ] File watcher tested
- [ ] Voice command tested (if using)
- [ ] Security settings configured
- [ ] Audit logging verified
- [ ] Monitor tool checked
- [ ] Production mode selected

**Your sovereign AI orchestration system is now ACTIVE!** 🎉
