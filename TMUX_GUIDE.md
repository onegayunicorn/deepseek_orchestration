# DeepSeek Orchestrator - Complete tmux Guide

This guide covers everything you need to know about using the tmux-based setup for the DeepSeek Orchestrator.

## 🚀 Quick Start

### Start All Services

```bash
bash tmux_setup.sh
```

This launches all services in an organized tmux session with 6 windows.

### Using Service Manager (Recommended)

```bash
# Start services
bash service_manager.sh start

# Check status
bash service_manager.sh status

# Attach to session
bash service_manager.sh attach

# Stop services
bash service_manager.sh stop

# Restart services
bash service_manager.sh restart

# View logs
bash service_manager.sh logs

# Run health check
bash service_manager.sh health
```

---

## 📊 Window Layout

When you start the orchestrator, you get 6 organized windows:

| Window | Name        | Purpose                          | Command                                    |
|--------|-------------|----------------------------------|--------------------------------------------|
| 0      | orchestrator| Main orchestrator (watch mode)   | `python3 deepseek_orchestrator.py --mode watch` |
| 1      | webapi      | REST API server                  | `python3 web_api.py`                       |
| 2      | voice       | Continuous voice listener        | `bash voice_listener.sh`                   |
| 3      | monitor     | Real-time health monitor         | `python3 monitor.py --watch`               |
| 4      | logs        | Live log viewer                  | `tail -f deepseek_orchestrator.log`        |
| 5      | shell       | Command shell for manual tasks   | `bash`                                     |

---

## 🎮 tmux Keyboard Shortcuts

### Essential Commands

All tmux commands start with the **prefix key**: `Ctrl+B`

Press `Ctrl+B`, release, then press the command key.

#### Window Navigation

| Shortcut          | Action                          |
|-------------------|---------------------------------|
| `Ctrl+B` then `0` | Switch to window 0 (orchestrator) |
| `Ctrl+B` then `1` | Switch to window 1 (webapi)     |
| `Ctrl+B` then `2` | Switch to window 2 (voice)      |
| `Ctrl+B` then `3` | Switch to window 3 (monitor)    |
| `Ctrl+B` then `4` | Switch to window 4 (logs)       |
| `Ctrl+B` then `5` | Switch to window 5 (shell)      |
| `Ctrl+B` then `n` | Next window                     |
| `Ctrl+B` then `p` | Previous window                 |
| `Ctrl+B` then `w` | List all windows (interactive)  |

#### Session Control

| Shortcut          | Action                          |
|-------------------|---------------------------------|
| `Ctrl+B` then `d` | Detach from session (keeps running) |
| `Ctrl+B` then `?` | Show all key bindings           |
| `Ctrl+B` then `:` | Enter command mode              |

#### Pane Management (Advanced)

| Shortcut          | Action                          |
|-------------------|---------------------------------|
| `Ctrl+B` then `%` | Split pane vertically           |
| `Ctrl+B` then `"` | Split pane horizontally         |
| `Ctrl+B` then `o` | Switch to next pane             |
| `Ctrl+B` then `x` | Close current pane              |

---

## 🔧 Service Manager Commands

### Basic Operations

```bash
# Start all services
bash service_manager.sh start

# Stop all services
bash service_manager.sh stop

# Restart all services
bash service_manager.sh restart

# Check status
bash service_manager.sh status

# Attach to running session
bash service_manager.sh attach
```

### Monitoring

```bash
# View live logs
bash service_manager.sh logs

# Run health check
bash service_manager.sh health

# List all windows
bash service_manager.sh windows
```

### Advanced

```bash
# Send command to specific window
bash service_manager.sh send 0 "echo 'Hello from window 0'"

# Send command to shell window
bash service_manager.sh send 5 "ls -la"
```

---

## 🏥 Health Checks

### Run Comprehensive Health Check

```bash
bash health_check.sh
```

This checks:
- System dependencies (tmux, Python, Termux:API)
- tmux session status
- Files and directories
- Logs and database
- Python modules
- Configuration validity
- Network services
- File permissions

### Quick Health Check

```bash
bash service_manager.sh health
```

---

## 🔄 Auto-Start on Boot

### Setup Auto-Start

1. **Create boot directory:**
   ```bash
   mkdir -p ~/.termux/boot
   ```

2. **Copy autostart script:**
   ```bash
   cp autostart.sh ~/.termux/boot/
   chmod +x ~/.termux/boot/autostart.sh
   ```

3. **Edit the script to set correct path:**
   ```bash
   nano ~/.termux/boot/autostart.sh
   ```
   
   Update the path to your installation directory.

4. **Install Termux:Boot app** from F-Droid

5. **Grant permissions** and enable auto-start in Android settings

Now services will start automatically when your device boots!

---

## 🐕 Watchdog (Auto-Recovery)

The watchdog monitors services and restarts them if they crash.

### Start Watchdog

```bash
bash watchdog.sh &
```

### Run Watchdog in Background

```bash
nohup bash watchdog.sh > watchdog_output.log 2>&1 &
```

### Check Watchdog Status

```bash
ps aux | grep watchdog
```

### Stop Watchdog

```bash
pkill -f watchdog.sh
```

### Watchdog Features

- Monitors tmux session every 60 seconds
- Automatically restarts crashed services
- Limits to 3 restart attempts per 5 minutes
- Sends notifications (if Termux:API installed)
- Logs all activity to `watchdog.log`

---

## 📱 Working with tmux from Outside

### Attach to Session

```bash
tmux attach -t deepseek
# or
bash service_manager.sh attach
```

### List Sessions

```bash
tmux ls
```

### Kill Session

```bash
tmux kill-session -t deepseek
# or
bash service_manager.sh stop
```

### Send Commands Without Attaching

```bash
# Send to specific window
tmux send-keys -t deepseek:0 "echo 'test'" C-m

# Using service manager
bash service_manager.sh send 0 "echo 'test'"
```

---

## 🎯 Common Workflows

### Workflow 1: Start and Monitor

```bash
# Start services
bash service_manager.sh start

# Services are now running in background
# Check status anytime
bash service_manager.sh status

# View logs
bash service_manager.sh logs
```

### Workflow 2: Interactive Session

```bash
# Start and attach immediately
bash tmux_setup.sh

# Navigate between windows
# Ctrl+B then 0-5 to switch

# Detach when done
# Ctrl+B then d

# Services keep running in background
```

### Workflow 3: Testing a Command

```bash
# Attach to session
bash service_manager.sh attach

# Switch to shell window
# Ctrl+B then 5

# Create a test task
echo "Show disk space" > triggers/test.task

# Switch to orchestrator window
# Ctrl+B then 0

# Watch it process

# Switch to monitor
# Ctrl+B then 3

# See statistics update
```

### Workflow 4: Debugging

```bash
# Attach to session
bash service_manager.sh attach

# Switch to logs window
# Ctrl+B then 4

# Watch live logs

# In another terminal, trigger actions
echo "Test command" > triggers/debug.task

# See logs update in real-time
```

---

## 🔍 Troubleshooting

### Services Won't Start

```bash
# Check if tmux is installed
which tmux

# Check if session already exists
tmux ls

# Kill existing session and retry
bash service_manager.sh stop
bash service_manager.sh start
```

### Can't Attach to Session

```bash
# Verify session exists
tmux ls

# If it exists, try:
tmux attach -t deepseek

# If it doesn't exist, start it:
bash service_manager.sh start
```

### Window is Unresponsive

```bash
# Attach to session
bash service_manager.sh attach

# Navigate to the window
# Ctrl+B then <window_number>

# Kill and restart the window
# Ctrl+B then :
# Type: kill-window
# Then manually restart that service in a new window
```

### Services Keep Crashing

```bash
# Run health check
bash health_check.sh

# Check logs
bash service_manager.sh logs

# Review configuration
nano config.json

# Start watchdog for auto-recovery
bash watchdog.sh &
```

---

## 📚 Advanced Tips

### Custom tmux Configuration

The included `.tmux.conf` provides enhanced settings:
- Mouse support enabled
- Better status bar
- Easier key bindings
- 256 color support

To use it:
```bash
cp .tmux.conf ~/.tmux.conf
tmux source-file ~/.tmux.conf
```

### Split Panes for Multi-View

While in a window:
```bash
# Split horizontally
Ctrl+B then "

# Split vertically
Ctrl+B then %

# Navigate between panes
Ctrl+B then arrow keys

# Close pane
Ctrl+B then x
```

### Create Additional Windows

```bash
# While in session
Ctrl+B then c

# Name the window
Ctrl+B then ,
# Type name and press Enter
```

### Scroll in tmux

```bash
# Enter copy mode
Ctrl+B then [

# Use arrow keys or Page Up/Down to scroll

# Press q to exit
```

---

## 🎓 Learning Resources

### Practice Commands

```bash
# Start session
bash service_manager.sh start

# Attach
bash service_manager.sh attach

# Practice switching windows
# Ctrl+B then 0, 1, 2, 3, 4, 5

# Detach
# Ctrl+B then d

# Reattach
bash service_manager.sh attach

# Stop
bash service_manager.sh stop
```

### tmux Cheat Sheet

Keep this handy:
- `Ctrl+B` then `?` - Show all bindings
- `Ctrl+B` then `d` - Detach
- `Ctrl+B` then `0-9` - Switch window
- `Ctrl+B` then `w` - Window list
- `Ctrl+B` then `[` - Scroll mode

---

## ✅ Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│            DeepSeek Orchestrator - tmux                 │
├─────────────────────────────────────────────────────────┤
│ Start:    bash service_manager.sh start                 │
│ Stop:     bash service_manager.sh stop                  │
│ Status:   bash service_manager.sh status                │
│ Attach:   bash service_manager.sh attach                │
│ Logs:     bash service_manager.sh logs                  │
│ Health:   bash health_check.sh                          │
├─────────────────────────────────────────────────────────┤
│ Window 0: Orchestrator (watch mode)                     │
│ Window 1: Web API (port 5000)                           │
│ Window 2: Voice Listener                                │
│ Window 3: Monitor (live stats)                          │
│ Window 4: Logs (live tail)                              │
│ Window 5: Shell (manual commands)                       │
├─────────────────────────────────────────────────────────┤
│ Ctrl+B then 0-5:  Switch window                         │
│ Ctrl+B then d:    Detach (keeps running)                │
│ Ctrl+B then ?:    Show help                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🎉 You're Ready!

You now have everything you need to manage your DeepSeek Orchestrator with tmux. Start simple with the service manager, then explore the advanced features as you get comfortable.

**Remember:** Services keep running even when you detach. This is perfect for long-running AI agents!
