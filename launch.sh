#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Universal Launcher
# Launch the orchestrator in various modes with a single command
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

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║        DeepSeek Orchestrator - Universal Launcher         ║"
    echo "║                                                            ║"
    echo "║    Sovereign AI Agent for Android/Termux                  ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Show menu
show_menu() {
    echo -e "${YELLOW}Available Modes:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} CLI Mode          - Interactive command line interface"
    echo -e "${GREEN}2)${NC} Watch Mode        - Monitor triggers directory for .task files"
    echo -e "${GREEN}3)${NC} Voice Mode        - Single voice command"
    echo -e "${GREEN}4)${NC} Voice Listener    - Continuous voice listening"
    echo -e "${GREEN}5)${NC} Web API           - Start REST API server"
    echo -e "${GREEN}6)${NC} Monitor           - System health monitor"
    echo -e "${GREEN}7)${NC} Audit Query       - Query audit logs"
    echo -e "${GREEN}8)${NC} Status            - Quick status check"
    echo ""
    echo -e "${CYAN}Advanced:${NC}"
    echo -e "${GREEN}9)${NC} All Services      - Start orchestrator + web API (tmux)"
    echo -e "${GREEN}10)${NC} Full Stack        - Start all services including voice (tmux)"
    echo ""
    echo -e "${MAGENTA}0)${NC} Exit"
    echo ""
}

# Check dependencies
check_dependencies() {
    local missing=()
    
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        missing+=("python3")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}Missing dependencies:${NC}"
        for dep in "${missing[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Run setup_termux.sh to install dependencies"
        return 1
    fi
    
    return 0
}

# Get Python command
get_python() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    else
        echo "python"
    fi
}

# Launch CLI mode
launch_cli() {
    echo -e "${GREEN}Starting CLI Mode...${NC}"
    echo ""
    $(get_python) deepseek_orchestrator.py --mode cli
}

# Launch watch mode
launch_watch() {
    echo -e "${GREEN}Starting Watch Mode...${NC}"
    echo "Watching: ./triggers/"
    echo ""
    $(get_python) deepseek_orchestrator.py --mode watch
}

# Launch voice command
launch_voice() {
    echo -e "${GREEN}Voice Command Mode${NC}"
    echo ""
    bash voice_command.sh
}

# Launch voice listener
launch_voice_listener() {
    echo -e "${GREEN}Starting Continuous Voice Listener...${NC}"
    echo ""
    bash voice_listener.sh
}

# Launch web API
launch_web_api() {
    echo -e "${GREEN}Starting Web API Server...${NC}"
    echo ""
    $(get_python) web_api.py
}

# Launch monitor
launch_monitor() {
    echo -e "${GREEN}Starting System Monitor...${NC}"
    echo ""
    $(get_python) monitor.py --watch
}

# Launch audit query
launch_audit() {
    echo -e "${GREEN}Audit Query Tool${NC}"
    echo ""
    echo "Recent events:"
    $(get_python) audit_query.py recent --limit 10
}

# Quick status
quick_status() {
    echo -e "${GREEN}Quick Status Check${NC}"
    echo ""
    $(get_python) monitor.py --json | $(get_python) -m json.tool
}

# Launch all services with tmux
launch_all_services() {
    if ! command -v tmux &> /dev/null; then
        echo -e "${RED}tmux not installed${NC}"
        echo "Install with: pkg install tmux"
        return 1
    fi
    
    echo -e "${GREEN}Starting All Services in tmux...${NC}"
    echo ""
    
    SESSION="deepseek_orchestrator"
    
    # Kill existing session if it exists
    tmux kill-session -t $SESSION 2>/dev/null
    
    # Create new session with orchestrator
    tmux new-session -d -s $SESSION -n orchestrator "$(get_python) deepseek_orchestrator.py --mode watch"
    
    # Create window for web API
    tmux new-window -t $SESSION -n webapi "$(get_python) web_api.py"
    
    # Create window for monitor
    tmux new-window -t $SESSION -n monitor "$(get_python) monitor.py --watch"
    
    # Select first window
    tmux select-window -t $SESSION:0
    
    echo -e "${GREEN}✓ Services started in tmux session: $SESSION${NC}"
    echo ""
    echo "Attach to session: tmux attach -t $SESSION"
    echo "Detach: Ctrl+B then D"
    echo "Switch windows: Ctrl+B then 0/1/2"
    echo "Kill session: tmux kill-session -t $SESSION"
    echo ""
    
    # Attach to session
    tmux attach -t $SESSION
}

# Launch full stack
launch_full_stack() {
    if ! command -v tmux &> /dev/null; then
        echo -e "${RED}tmux not installed${NC}"
        echo "Install with: pkg install tmux"
        return 1
    fi
    
    echo -e "${GREEN}Starting Full Stack in tmux...${NC}"
    echo ""
    
    SESSION="deepseek_full"
    
    # Kill existing session if it exists
    tmux kill-session -t $SESSION 2>/dev/null
    
    # Create new session with orchestrator
    tmux new-session -d -s $SESSION -n orchestrator "$(get_python) deepseek_orchestrator.py --mode watch"
    
    # Create window for web API
    tmux new-window -t $SESSION -n webapi "$(get_python) web_api.py"
    
    # Create window for voice listener
    tmux new-window -t $SESSION -n voice "bash voice_listener.sh"
    
    # Create window for monitor
    tmux new-window -t $SESSION -n monitor "$(get_python) monitor.py --watch"
    
    # Select first window
    tmux select-window -t $SESSION:0
    
    echo -e "${GREEN}✓ Full stack started in tmux session: $SESSION${NC}"
    echo ""
    echo "Services running:"
    echo "  - Window 0: Orchestrator (watch mode)"
    echo "  - Window 1: Web API"
    echo "  - Window 2: Voice Listener"
    echo "  - Window 3: Monitor"
    echo ""
    echo "Attach to session: tmux attach -t $SESSION"
    echo "Detach: Ctrl+B then D"
    echo "Switch windows: Ctrl+B then 0/1/2/3"
    echo "Kill session: tmux kill-session -t $SESSION"
    echo ""
    
    # Attach to session
    tmux attach -t $SESSION
}

# Main
main() {
    show_banner
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # If argument provided, launch directly
    if [ $# -gt 0 ]; then
        case "$1" in
            cli)
                launch_cli
                ;;
            watch)
                launch_watch
                ;;
            voice)
                launch_voice
                ;;
            voice-listener)
                launch_voice_listener
                ;;
            web)
                launch_web_api
                ;;
            monitor)
                launch_monitor
                ;;
            audit)
                launch_audit
                ;;
            status)
                quick_status
                ;;
            all)
                launch_all_services
                ;;
            full)
                launch_full_stack
                ;;
            *)
                echo -e "${RED}Unknown mode: $1${NC}"
                echo ""
                echo "Usage: $0 [cli|watch|voice|voice-listener|web|monitor|audit|status|all|full]"
                exit 1
                ;;
        esac
        exit 0
    fi
    
    # Interactive menu
    while true; do
        show_menu
        read -p "Select mode (0-10): " choice
        echo ""
        
        case $choice in
            1)
                launch_cli
                ;;
            2)
                launch_watch
                ;;
            3)
                launch_voice
                ;;
            4)
                launch_voice_listener
                ;;
            5)
                launch_web_api
                ;;
            6)
                launch_monitor
                ;;
            7)
                launch_audit
                ;;
            8)
                quick_status
                read -p "Press Enter to continue..."
                clear
                show_banner
                ;;
            9)
                launch_all_services
                ;;
            10)
                launch_full_stack
                ;;
            0)
                echo -e "${CYAN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice${NC}"
                sleep 1
                clear
                show_banner
                ;;
        esac
    done
}

main "$@"
