#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Complete tmux Setup
# Automatically launches all services in organized tmux sessions
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SESSION_NAME="deepseek"
PYTHON_CMD="python3"

# Check if python3 exists, fallback to python
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Banner
echo -e "${CYAN}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     DeepSeek Orchestrator - Complete tmux Setup           ║
║                                                            ║
║     Launching all services in organized sessions          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}Error: tmux is not installed${NC}"
    echo ""
    echo "Install with: pkg install tmux"
    exit 1
fi

echo -e "${GREEN}✓ tmux detected${NC}"

# Check if session already exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${YELLOW}Session '$SESSION_NAME' already exists${NC}"
    echo ""
    read -p "Kill existing session and restart? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Killing existing session...${NC}"
        tmux kill-session -t "$SESSION_NAME"
        sleep 1
    else
        echo -e "${CYAN}Attaching to existing session...${NC}"
        tmux attach -t "$SESSION_NAME"
        exit 0
    fi
fi

echo ""
echo -e "${CYAN}Creating tmux session: $SESSION_NAME${NC}"
echo ""

# Create new detached session with orchestrator
echo -e "${YELLOW}[1/6] Starting Orchestrator (watch mode)...${NC}"
tmux new-session -d -s "$SESSION_NAME" -n orchestrator \
    "cd '$SCRIPT_DIR' && $PYTHON_CMD deepseek_orchestrator.py --mode watch"

sleep 1

# Create window for web API
echo -e "${YELLOW}[2/6] Starting Web API...${NC}"
tmux new-window -t "$SESSION_NAME" -n webapi \
    "cd '$SCRIPT_DIR' && $PYTHON_CMD web_api.py"

sleep 1

# Create window for voice listener
echo -e "${YELLOW}[3/6] Starting Voice Listener...${NC}"
tmux new-window -t "$SESSION_NAME" -n voice \
    "cd '$SCRIPT_DIR' && bash voice_listener.sh"

sleep 1

# Create window for monitor
echo -e "${YELLOW}[4/6] Starting Monitor...${NC}"
tmux new-window -t "$SESSION_NAME" -n monitor \
    "cd '$SCRIPT_DIR' && $PYTHON_CMD monitor.py --watch --interval 10"

sleep 1

# Create window for logs
echo -e "${YELLOW}[5/6] Creating Logs viewer...${NC}"
tmux new-window -t "$SESSION_NAME" -n logs \
    "cd '$SCRIPT_DIR' && tail -f deepseek_orchestrator.log 2>/dev/null || echo 'Waiting for log file...' && sleep infinity"

sleep 1

# Create window for shell/commands
echo -e "${YELLOW}[6/6] Creating Command shell...${NC}"
tmux new-window -t "$SESSION_NAME" -n shell \
    "cd '$SCRIPT_DIR' && bash"

# Set default window
tmux select-window -t "$SESSION_NAME":0

echo ""
echo -e "${GREEN}✓ All services started successfully!${NC}"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Session Layout                          ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Window 0 (orchestrator):${NC} Main orchestrator in watch mode"
echo -e "${GREEN}Window 1 (webapi):${NC}       REST API server on port 5000"
echo -e "${GREEN}Window 2 (voice):${NC}        Continuous voice listener"
echo -e "${GREEN}Window 3 (monitor):${NC}      Real-time health monitor"
echo -e "${GREEN}Window 4 (logs):${NC}         Live log viewer"
echo -e "${GREEN}Window 5 (shell):${NC}        Command shell for manual tasks"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    tmux Commands                           ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Navigation:${NC}"
echo -e "  Ctrl+B then 0-5     Switch to window 0-5"
echo -e "  Ctrl+B then n       Next window"
echo -e "  Ctrl+B then p       Previous window"
echo -e "  Ctrl+B then w       List all windows"
echo ""
echo -e "${YELLOW}Session Control:${NC}"
echo -e "  Ctrl+B then d       Detach from session (services keep running)"
echo -e "  Ctrl+B then :       Enter command mode"
echo -e "  Ctrl+B then ?       Show all key bindings"
echo ""
echo -e "${YELLOW}From Outside Session:${NC}"
echo -e "  tmux attach -t $SESSION_NAME    Reattach to session"
echo -e "  tmux ls                         List all sessions"
echo -e "  tmux kill-session -t $SESSION_NAME  Stop all services"
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Quick Actions                           ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Test the system:${NC}"
echo -e "  1. Switch to window 5 (shell): Ctrl+B then 5"
echo -e "  2. Create a test task: echo 'Show disk space' > triggers/test.task"
echo -e "  3. Switch to window 0 (orchestrator): Ctrl+B then 0"
echo -e "  4. Watch it process the command"
echo -e "  5. Switch to window 3 (monitor): Ctrl+B then 3"
echo -e "  6. See the statistics update"
echo ""
echo -e "${YELLOW}Press Enter to attach to the session...${NC}"
read

# Attach to session
tmux attach -t "$SESSION_NAME"
