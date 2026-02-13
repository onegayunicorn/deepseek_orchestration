#!/bin/bash
# DeepSeek Orchestrator Setup Script for Termux/Android
# This script installs all dependencies and sets up the environment

set -e  # Exit on error

echo "=========================================="
echo "DeepSeek Orchestrator Setup for Termux"
echo "=========================================="
echo ""

# Update package lists
echo "[1/7] Updating package lists..."
pkg update -y

# Install Python and essential tools
echo "[2/7] Installing Python and essential packages..."
pkg install -y python python-pip git wget

# Install optional but recommended packages
echo "[3/7] Installing optional tools..."
pkg install -y termux-api sqlite

# Upgrade pip
echo "[4/7] Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "[5/7] Installing Python dependencies..."
pip install watchdog

# Optional: Install llama-cpp-python (may take a while to compile)
echo "[6/7] Installing llama-cpp-python (this may take several minutes)..."
echo "Note: This requires compilation and may fail on some devices."
echo "If it fails, the orchestrator will run in mock mode."
read -p "Install llama-cpp-python? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install llama-cpp-python || echo "Warning: llama-cpp-python installation failed. Mock mode will be used."
else
    echo "Skipping llama-cpp-python installation. Mock mode will be used."
fi

# Create directory structure
echo "[7/7] Creating directory structure..."
mkdir -p ~/deepseek_orchestration/triggers
cd ~/deepseek_orchestration

# Download orchestrator files (if not already present)
if [ ! -f "deepseek_orchestrator.py" ]; then
    echo "Note: Copy the orchestrator files to ~/deepseek_orchestration/"
    echo "Required files:"
    echo "  - deepseek_orchestrator.py"
    echo "  - config.json"
fi

# Create a sample config if it doesn't exist
if [ ! -f "config.json" ]; then
    cat > config.json << 'EOF'
{
  "model_path": null,
  "context_size": 2048,
  "execution_mode": "prompt",
  "timeout": 30,
  "security": {
    "whitelist": [
      "ls", "cat", "echo", "pwd", "date", "whoami",
      "df", "du", "ps", "top", "grep", "find", "wc", "head", "tail"
    ],
    "blacklist": [
      "rm -rf /", "dd if=", "> /dev/", "chmod 777",
      "curl | sh", "wget | sh", "mkfs"
    ],
    "require_approval_for": [
      "docker", "git", "pkg", "apt", "npm", "pip",
      "chmod", "chown", "kill", "pkill"
    ]
  },
  "audit_log": "deepseek_audit.db"
}
EOF
    echo "Created default config.json"
fi

# Make orchestrator executable
if [ -f "deepseek_orchestrator.py" ]; then
    chmod +x deepseek_orchestrator.py
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. If you have a GGUF model, update 'model_path' in config.json"
echo "2. Run in CLI mode: python deepseek_orchestrator.py --mode cli"
echo "3. Run in watch mode: python deepseek_orchestrator.py --mode watch"
echo ""
echo "For mock mode (no model required), just run without setting model_path."
echo ""
echo "Directory structure:"
echo "  ~/deepseek_orchestration/"
echo "    ├── deepseek_orchestrator.py  (main script)"
echo "    ├── config.json                (configuration)"
echo "    ├── triggers/                  (watched directory for .task/.flag files)"
echo "    ├── deepseek_audit.db          (audit log database, created on first run)"
echo "    └── deepseek_orchestrator.log  (runtime log, created on first run)"
echo ""
echo "Documentation:"
echo "  - See examples.md for usage examples"
echo "  - See architecture.md for system design"
echo ""
