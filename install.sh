#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator + AlienPC Ω Mesh - Unified Installer
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🦅 DeepSeek Orchestrator + AlienPC Ω Mesh Installer${NC}"
echo "----------------------------------------------------"

# 1. System Check
echo -e "${YELLOW}[1/5] Checking environment...${NC}"
if [ -d "/data/data/com.termux" ]; then
    echo "✓ Termux environment detected"
else
    echo "⚠ Not a Termux environment, proceeding with standard Linux install"
fi

# 2. Dependencies
echo -e "${YELLOW}[2/5] Installing dependencies...${NC}"
if command -v pkg &> /dev/null; then
    pkg update && pkg upgrade -y
    pkg install -y git gh tmux python gnupg nodejs openssh
else
    sudo apt-get update
    sudo apt-get install -y git tmux python3 python3-pip gnupg nodejs openssh-server
fi

# 3. Python Packages
echo -e "${YELLOW}[3/5] Installing Python packages...${NC}"
pip install -r requirements.txt || pip3 install -r requirements.txt --break-system-packages

# 4. Setup Directories
echo -e "${YELLOW}[4/5] Setting up directories...${NC}"
mkdir -p triggers logs_archive

# 5. Initialize Council Keys
echo -e "${YELLOW}[5/5] Initializing Council Governance...${NC}"
if [ -f "alienpc_integration.py" ]; then
    echo "✓ Integration scripts detected"
fi

echo ""
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo ""
echo -e "To start the system:"
echo -e "  ${CYAN}bash service_manager.sh start${NC}"
echo ""
echo -e "To view the dashboard:"
echo -e "  ${CYAN}http://localhost:5000/dashboard${NC}"
echo ""
echo -e "To manage with tmux:"
echo -e "  ${CYAN}bash service_manager.sh attach${NC}"
echo ""
