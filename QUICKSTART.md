# Quick Start Guide

Get up and running with the DeepSeek Orchestrator in just a few minutes.

## 1. Installation (5 minutes)

Transfer all files to your Android device and run the setup script in Termux:

```bash
bash ~/deepseek_orchestration/setup_termux.sh
```

When prompted about installing `llama-cpp-python`, choose:
- **Yes** if you have a GGUF model file and want real AI inference
- **No** if you want to test the system first in mock mode

## 2. First Run (1 minute)

Start the orchestrator in interactive mode:

```bash
cd ~/deepseek_orchestration
python deepseek_orchestrator.py --mode cli
```

## 3. Try Your First Command (30 seconds)

Type a natural language request:

```
>>> Show me the current directory
```

The orchestrator will:
1. Ask DeepSeek (or use mock mode) to suggest a command
2. Show you the suggested command (e.g., `pwd`)
3. Ask for your approval
4. Execute the command
5. Display the results

## 4. Test File Watcher Mode (2 minutes)

Open a new Termux session and start the file watcher:

```bash
cd ~/deepseek_orchestration
python deepseek_orchestrator.py --mode watch
```

In another Termux session, create a trigger file:

```bash
echo "List all Python files" > ~/deepseek_orchestration/triggers/find_python.task
```

The orchestrator will automatically detect the file, process the request, and create a `.result` file with the output.

## 5. Review the Audit Log (1 minute)

Check what the orchestrator has done:

```bash
sqlite3 ~/deepseek_orchestration/deepseek_audit.db "SELECT timestamp, suggested_command, executed FROM audit_log;"
```

## Next Steps

- **Add a Real Model**: If you have a GGUF model file, update `model_path` in `config.json`
- **Customize Security**: Edit the `whitelist`, `blacklist`, and `require_approval_for` lists in `config.json`
- **Explore Examples**: See `examples.md` for 15+ usage scenarios
- **Read the Docs**: Check `README.md` for the complete documentation

## Troubleshooting

**Problem**: "Command not found" errors
- **Solution**: Make sure you ran the setup script and all dependencies are installed

**Problem**: Model loading fails
- **Solution**: Verify the `model_path` in `config.json` points to a valid GGUF file, or set it to `null` for mock mode

**Problem**: Permission denied errors
- **Solution**: Termux doesn't use `sudo`. Remove any `sudo` commands from your whitelist

**Problem**: Commands aren't executing
- **Solution**: Check your `execution_mode` in `config.json`. If it's `audit_only` or `dry_run`, change it to `prompt`

## Safety Reminder

Always review suggested commands before approving them. Start with `prompt` mode and only switch to `auto_approve` after you're confident in the system's behavior.
