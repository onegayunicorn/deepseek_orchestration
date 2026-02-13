#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Service Manager
# Manage tmux-based services with systemd-like commands
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SESSION_NAME="deepseek"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check if tmux is installed
check_tmux() {
    if ! command -v tmux &> /dev/null; then
        echo -e "${RED}Error: tmux is not installed${NC}"
        echo "Install with: pkg install tmux"
        exit 1
    fi
}

# Check if session exists
session_exists() {
    tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

# Start services
start_services() {
    if session_exists; then
        echo -e "${YELLOW}Services are already running${NC}"
        echo "Use 'status' to check or 'restart' to restart"
        return 1
    fi
    
    echo -e "${GREEN}Starting DeepSeek Orchestrator services...${NC}"
    bash "$SCRIPT_DIR/tmux_setup.sh"
}

# Stop services
stop_services() {
    if ! session_exists; then
        echo -e "${YELLOW}Services are not running${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Stopping DeepSeek Orchestrator services...${NC}"
    tmux kill-session -t "$SESSION_NAME"
    echo -e "${GREEN}✓ Services stopped${NC}"
}

# Restart services
restart_services() {
    echo -e "${CYAN}Restarting DeepSeek Orchestrator services...${NC}"
    stop_services
    sleep 2
    start_services
}

# Show status
show_status() {
    echo -e "${CYAN}DeepSeek Orchestrator Status${NC}"
    echo -e "${CYAN}=============================${NC}"
    echo ""
    
    if session_exists; then
        echo -e "${GREEN}● Services: RUNNING${NC}"
        echo ""
        echo "Session: $SESSION_NAME"
        echo ""
        echo "Windows:"
        tmux list-windows -t "$SESSION_NAME" -F "  #{window_index}: #{window_name} (#{pane_current_command})"
        echo ""
        echo "Panes:"
        tmux list-panes -t "$SESSION_NAME" -a -F "  Window #{window_index}: #{pane_current_command} - #{pane_pid}"
        echo ""
        echo -e "${CYAN}Commands:${NC}"
        echo "  Attach:  $0 attach"
        echo "  Stop:    $0 stop"
        echo "  Restart: $0 restart"
    else
        echo -e "${RED}● Services: STOPPED${NC}"
        echo ""
        echo -e "${CYAN}Commands:${NC}"
        echo "  Start:   $0 start"
    fi
}

# Attach to session
attach_session() {
    if ! session_exists; then
        echo -e "${RED}Services are not running${NC}"
        echo "Start with: $0 start"
        return 1
    fi
    
    tmux attach -t "$SESSION_NAME"
}

# Show logs
show_logs() {
    if [ -f "$SCRIPT_DIR/deepseek_orchestrator.log" ]; then
        tail -f "$SCRIPT_DIR/deepseek_orchestrator.log"
    else
        echo -e "${YELLOW}Log file not found yet${NC}"
        echo "Services may not have started yet"
    fi
}

# List windows
list_windows() {
    if ! session_exists; then
        echo -e "${RED}Services are not running${NC}"
        return 1
    fi
    
    echo -e "${CYAN}Active Windows:${NC}"
    tmux list-windows -t "$SESSION_NAME"
}

# Send command to specific window
send_command() {
    local window=$1
    local command=$2
    
    if ! session_exists; then
        echo -e "${RED}Services are not running${NC}"
        return 1
    fi
    
    if [ -z "$window" ] || [ -z "$command" ]; then
        echo "Usage: $0 send <window_number> <command>"
        return 1
    fi
    
    tmux send-keys -t "$SESSION_NAME:$window" "$command" C-m
    echo -e "${GREEN}✓ Command sent to window $window${NC}"
}

# Self-healing watchdog mode
watchdog_mode() {
    echo -e "${CYAN}Starting Self-Healing Watchdog...${NC}"
    echo "Interval: 60s"
    
    while true; do
        if ! session_exists; then
            echo -e "${RED}[$(date)] Session died! Restarting...${NC}"
            start_services
        else
            # Check individual windows
            WINDOWS=$(tmux list-windows -t "$SESSION_NAME" -F "#W" 2>/dev/null)
            for SERVICE in orchestrator webapi voice monitor logs; do
                if [[ ! "$WINDOWS" =~ "$SERVICE" ]]; then
                    echo -e "${YELLOW}[$(date)] Service $SERVICE missing! Restoring...${NC}"
                    case $SERVICE in
                        orchestrator) tmux new-window -t "$SESSION_NAME" -n orchestrator "cd '$SCRIPT_DIR' && $PYTHON_CMD deepseek_orchestrator.py --mode watch" ;;
                        webapi) tmux new-window -t "$SESSION_NAME" -n webapi "cd '$SCRIPT_DIR' && $PYTHON_CMD web_api.py" ;;
                        voice) tmux new-window -t "$SESSION_NAME" -n voice "cd '$SCRIPT_DIR' && bash voice_listener.sh" ;;
                        monitor) tmux new-window -t "$SESSION_NAME" -n monitor "cd '$SCRIPT_DIR' && $PYTHON_CMD monitor.py --watch" ;;
                        logs) tmux new-window -t "$SESSION_NAME" -n logs "cd '$SCRIPT_DIR' && tail -f deepseek_orchestrator.log" ;;
                    esac
                fi
            done
        fi
        sleep 60
    done
}

# Health check
health_check() {
    echo -e "${CYAN}Running health check...${NC}"
    echo ""
    
    if ! session_exists; then
        echo -e "${RED}✗ Services are not running${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ tmux session is active${NC}"
    
    # Check if orchestrator log exists and has recent activity
    if [ -f "$SCRIPT_DIR/deepseek_orchestrator.log" ]; then
        local log_age=$(( $(date +%s) - $(stat -c %Y "$SCRIPT_DIR/deepseek_orchestrator.log" 2>/dev/null || stat -f %m "$SCRIPT_DIR/deepseek_orchestrator.log" 2>/dev/null || echo 0) ))
        if [ $log_age -lt 300 ]; then
            echo -e "${GREEN}✓ Orchestrator is active (log updated ${log_age}s ago)${NC}"
        else
            echo -e "${YELLOW}⚠ Orchestrator may be idle (log updated ${log_age}s ago)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Orchestrator log not found${NC}"
    fi
    
    # Check if audit database exists
    if [ -f "$SCRIPT_DIR/deepseek_audit.db" ]; then
        echo -e "${GREEN}✓ Audit database exists${NC}"
    else
        echo -e "${YELLOW}⚠ Audit database not created yet${NC}"
    fi
    
    # Check triggers directory
    if [ -d "$SCRIPT_DIR/triggers" ]; then
        local pending=$(ls "$SCRIPT_DIR/triggers"/*.task 2>/dev/null | wc -l)
        local results=$(ls "$SCRIPT_DIR/triggers"/*.result 2>/dev/null | wc -l)
        echo -e "${GREEN}✓ Triggers directory exists${NC}"
        echo "  Pending tasks: $pending"
        echo "  Completed results: $results"
    else
        echo -e "${YELLOW}⚠ Triggers directory not found${NC}"
    fi
}

# Show help
show_help() {
    cat << EOF
${CYAN}DeepSeek Orchestrator - Service Manager${NC}

${YELLOW}Usage:${NC}
  $0 <command>

${YELLOW}Commands:${NC}
  start       Start all services in tmux
  stop        Stop all services
  restart     Restart all services
  status      Show service status
  attach      Attach to tmux session
  logs        Show live logs
  windows     List all windows
  send        Send command to window
  health      Run health check
  watchdog    Start self-healing watchdog
  help        Show this help

${YELLOW}Examples:${NC}
  $0 start                    # Start all services
  $0 status                   # Check if services are running
  $0 attach                   # Attach to tmux session
  $0 logs                     # View live logs
  $0 send 0 "echo test"       # Send command to window 0
  $0 health                   # Run health check
  $0 restart                  # Restart all services

${YELLOW}Window Layout:${NC}
  0: orchestrator - Main orchestrator (watch mode)
  1: webapi       - REST API server
  2: voice        - Voice listener
  3: monitor      - Health monitor
  4: logs         - Log viewer
  5: shell        - Command shell

${YELLOW}tmux Quick Reference:${NC}
  Ctrl+B then 0-5     Switch to window
  Ctrl+B then d       Detach (services keep running)
  Ctrl+B then w       List windows
  Ctrl+B then ?       Show all keybindings

EOF
}

# Main
main() {
    check_tmux
    
    case "${1:-help}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        attach)
            attach_session
            ;;
        logs)
            show_logs
            ;;
        windows)
            list_windows
            ;;
        send)
            send_command "$2" "$3"
            ;;
        health)
            health_check
            ;;
        watchdog)
            watchdog_mode
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
