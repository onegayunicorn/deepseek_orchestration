#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Watchdog
# Monitors services and restarts them if they crash
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SESSION_NAME="deepseek"
CHECK_INTERVAL=60  # Check every 60 seconds
MAX_RESTARTS=3
RESTART_COUNT=0
RESTART_WINDOW=300  # Reset counter after 5 minutes

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

LOG_FILE="$SCRIPT_DIR/watchdog.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

notify() {
    if command -v termux-notification &> /dev/null; then
        termux-notification --title "DeepSeek Watchdog" --content "$1"
    fi
}

check_session() {
    tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

restart_services() {
    log "${YELLOW}Attempting to restart services...${NC}"
    notify "Services crashed, attempting restart"
    
    bash "$SCRIPT_DIR/service_manager.sh" start
    
    if [ $? -eq 0 ]; then
        log "${GREEN}✓ Services restarted successfully${NC}"
        notify "Services restarted successfully"
        return 0
    else
        log "${RED}✗ Failed to restart services${NC}"
        notify "Failed to restart services"
        return 1
    fi
}

log "${CYAN}DeepSeek Orchestrator Watchdog started${NC}"
log "Monitoring session: $SESSION_NAME"
log "Check interval: ${CHECK_INTERVAL}s"
log "Max restarts: $MAX_RESTARTS per ${RESTART_WINDOW}s"

LAST_RESTART_TIME=0

while true; do
    if ! check_session; then
        log "${RED}✗ Session not found!${NC}"
        
        # Check if we're within restart limits
        CURRENT_TIME=$(date +%s)
        TIME_SINCE_LAST_RESTART=$((CURRENT_TIME - LAST_RESTART_TIME))
        
        # Reset counter if enough time has passed
        if [ $TIME_SINCE_LAST_RESTART -gt $RESTART_WINDOW ]; then
            RESTART_COUNT=0
            log "Reset restart counter (${TIME_SINCE_LAST_RESTART}s elapsed)"
        fi
        
        if [ $RESTART_COUNT -lt $MAX_RESTARTS ]; then
            RESTART_COUNT=$((RESTART_COUNT + 1))
            log "Restart attempt $RESTART_COUNT of $MAX_RESTARTS"
            
            if restart_services; then
                LAST_RESTART_TIME=$CURRENT_TIME
            else
                log "${RED}Restart failed, will retry in ${CHECK_INTERVAL}s${NC}"
            fi
        else
            log "${RED}Max restart attempts reached, giving up${NC}"
            notify "Services failed to restart after $MAX_RESTARTS attempts"
            exit 1
        fi
    else
        # Session is running, check health
        WINDOW_COUNT=$(tmux list-windows -t "$SESSION_NAME" 2>/dev/null | wc -l)
        
        if [ "$WINDOW_COUNT" -lt 4 ]; then
            log "${YELLOW}⚠ Warning: Only $WINDOW_COUNT windows running (expected 6)${NC}"
        fi
    fi
    
    sleep "$CHECK_INTERVAL"
done
