# 🦅 DeepSeek Orchestrator - Sovereign AI for Android/Termux

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Termux](https://img.shields.io/badge/Platform-Termux-green.svg)](https://termux.dev/)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

A complete, production-ready orchestration system that bridges local DeepSeek language models to live system execution on Android devices. Transform your phone into a sovereign AI agent with voice control, file-based automation, and comprehensive security.

## 🌟 Features

### Core Capabilities
- **🤖 Local AI Inference**: Run DeepSeek models entirely on-device with GGUF support
- **🎤 Voice Integration**: Hands-free operation with Termux:API speech-to-text
- **📁 File-Based Triggers**: Drop `.task` files to queue commands from any app
- **🌐 REST API**: HTTP interface for remote control and integration
- **🔒 Multi-Layer Security**: Whitelist/blacklist, user approval, command sanitization
- **📊 Complete Audit Trail**: SQLite database logs every action
- **📈 Real-Time Monitoring**: Live dashboard for health and performance
- **🔄 Multiple Execution Modes**: Prompt, auto-approve, dry-run, audit-only

### Advanced Features
- **Mock Mode**: Test without a model for development
- **Batch Processing**: Submit multiple commands at once
- **Priority Queuing**: High/normal/low priority task handling
- **Rate Limiting**: Prevent rapid-fire command execution
- **Wake-Word Detection**: Voice commands require "Orchestrator" prefix
- **tmux Integration**: Run all services in organized terminal sessions
- **Comprehensive Tooling**: CLI, monitoring, audit queries, app bridges

## 🚀 Quick Start

### Prerequisites
- Android device with Termux (from F-Droid)
- Termux:API app (for voice features)
- 2GB+ free storage (4-8GB for full models)

### Installation

```bash
# Clone repository
cd ~
gh repo clone onegayunicorn/deepseek_orchestration
cd deepseek_orchestration

# Run setup
bash setup_termux.sh

# Launch orchestrator
bash launch.sh
```

**That's it!** Select a mode from the menu and start using your AI agent.

## 📖 Documentation

- **[ACTIVATION_GUIDE.md](ACTIVATION_GUIDE.md)** - Complete setup and activation walkthrough
- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[README.md](README.md)** - Detailed system documentation
- **[examples.md](examples.md)** - 15+ usage scenarios and code samples
- **[architecture.md](architecture.md)** - System design and component details

## 🎯 Usage Modes

### 1. Interactive CLI
```bash
bash launch.sh cli
```
Type natural language commands and approve execution.

### 2. File Watcher
```bash
bash launch.sh watch
```
Monitor `triggers/` directory for `.task` files.

### 3. Voice Control
```bash
bash launch.sh voice
```
Say: "Orchestrator, show disk space"

### 4. Web API
```bash
bash launch.sh web
```
REST API on `http://localhost:5000`

### 5. Full Stack (tmux)
```bash
bash launch.sh full
```
All services running: orchestrator + API + voice + monitor

## 🔧 Configuration

Edit `config.json` to customize:

```json
{
  "model_path": "/path/to/model.gguf",
  "execution_mode": "prompt",
  "security": {
    "whitelist": ["ls", "cat", "echo", "pwd"],
    "blacklist": ["rm -rf", "dd", "mkfs"],
    "require_approval_for": ["docker", "git", "chmod"]
  },
  "voice": {
    "enabled": true,
    "wake_word": "orchestrator"
  }
}
```

## 🛡️ Security

Security is built into every layer:

1. **Command Validation**: Whitelist/blacklist filtering
2. **User Approval**: Explicit confirmation for sensitive operations
3. **Sanitization**: Input cleaning to prevent injection
4. **Audit Logging**: Complete record of all actions
5. **Rate Limiting**: Prevent abuse and rapid execution
6. **Wake-Word**: Voice commands require specific prefix

**Default mode is `prompt`** - you approve every command.

## 📊 Project Structure

```
deepseek_orchestration/
├── deepseek_orchestrator.py  # Core orchestrator engine
├── config.json                # Configuration file
├── launch.sh                  # Universal launcher
├── setup_termux.sh           # Installation script
├── voice_command.sh          # Voice input handler
├── voice_listener.sh         # Continuous voice mode
├── app_bridge.py             # External app integration
├── web_api.py                # REST API server
├── monitor.py                # Health monitoring tool
├── audit_query.py            # Audit log analysis
├── triggers/                 # Watched directory for tasks
├── workflow.png              # System workflow diagram
└── architecture_diagram.png  # Component architecture
```

## 🔗 Integration Examples

### Python App
```python
from app_bridge import AppBridge

bridge = AppBridge()
task = bridge.submit_command("Show system uptime", source="my_app")
result = bridge.wait_for_result(task, timeout=30)
print(result['output'])
```

### cURL (Web API)
```bash
curl -X POST http://localhost:5000/api/v1/execute \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"command": "Show disk space", "wait": true}'
```

### Bash Script
```bash
echo "List all Python files" > triggers/find_python.task
# Orchestrator processes and creates find_python.result
```

## 🎓 Use Cases

- **DevOps Automation**: Deploy, monitor, and manage services
- **System Administration**: Scheduled maintenance and monitoring
- **Voice Assistant**: Hands-free device control
- **App Integration**: Connect any app to system commands
- **Research & Development**: Test AI-driven automation safely
- **Personal Productivity**: Automate repetitive tasks
- **Offline AI Agent**: Complete sovereignty, no cloud required

## 📈 Monitoring & Maintenance

### Quick Status
```bash
bash launch.sh status
```

### Live Monitor
```bash
python3 monitor.py --watch
```

### Audit Logs
```bash
python3 audit_query.py recent --limit 20
python3 audit_query.py stats
```

## 🐛 Troubleshooting

### Model won't load
Set `model_path` to `null` in `config.json` for mock mode.

### Voice not working
1. Install Termux:API from F-Droid
2. Grant microphone permissions
3. Test: `termux-microphone-record -d 3 -f test.wav`

### Commands not executing
Check `execution_mode` in config. Use `"prompt"` for testing.

See [ACTIVATION_GUIDE.md](ACTIVATION_GUIDE.md) for complete troubleshooting.

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional LLM backends (Ollama, LM Studio API)
- Enhanced voice processing (Vosk, Whisper)
- Web UI dashboard
- Android app wrapper
- Additional security features
- Performance optimizations

## 📜 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- DeepSeek AI for the language models
- Termux project for Android Linux environment
- llama.cpp for efficient inference
- The open-source community

## 🔮 Roadmap

- [ ] Web UI dashboard with real-time updates
- [ ] Native Android app wrapper
- [ ] Multi-model support (switch between models)
- [ ] Enhanced voice with Vosk/Whisper
- [ ] Learning from user feedback
- [ ] Distributed execution across devices
- [ ] Plugin system for extensions
- [ ] Docker container version

## 📞 Support

- **Documentation**: See docs in repository
- **Issues**: GitHub Issues for bugs/features
- **Discussions**: GitHub Discussions for questions
- **Security**: Report vulnerabilities privately

---

**Built with ❤️ for sovereign AI computing**

Transform your Android device into a powerful, private AI agent. No cloud. No data leaks. Complete control.

🦅 **Your device. Your AI. Your rules.**
