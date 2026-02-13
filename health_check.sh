#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Comprehensive Health Check
# Performs detailed health checks on all components
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SESSION_NAME="deepseek"
PYTHON_CMD="python3"

if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
WARN=0
FAIL=0

check() {
    local name="$1"
    local status="$2"
    local message="$3"
    
    case "$status" in
        pass)
            echo -e "${GREEN}✓${NC} $name: $message"
            PASS=$((PASS + 1))
            ;;
        warn)
            echo -e "${YELLOW}⚠${NC} $name: $message"
            WARN=$((WARN + 1))
            ;;
        fail)
            echo -e "${RED}✗${NC} $name: $message"
            FAIL=$((FAIL + 1))
            ;;
    esac
}

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     DeepSeek Orchestrator - Health Check Report           ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}[1/8] System Dependencies${NC}"
echo ""

# Check tmux
if command -v tmux &> /dev/null; then
    check "tmux" "pass" "Installed ($(tmux -V))"
else
    check "tmux" "fail" "Not installed"
fi

# Check Python
if command -v $PYTHON_CMD &> /dev/null; then
    check "Python" "pass" "Installed ($($PYTHON_CMD --version))"
else
    check "Python" "fail" "Not installed"
fi

# Check Termux:API (optional)
if command -v termux-microphone-record &> /dev/null; then
    check "Termux:API" "pass" "Installed (voice features available)"
else
    check "Termux:API" "warn" "Not installed (voice features unavailable)"
fi

echo ""
echo -e "${CYAN}[2/8] tmux Session${NC}"
echo ""

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    check "Session" "pass" "Running ($SESSION_NAME)"
    
    WINDOW_COUNT=$(tmux list-windows -t "$SESSION_NAME" 2>/dev/null | wc -l)
    if [ "$WINDOW_COUNT" -ge 6 ]; then
        check "Windows" "pass" "$WINDOW_COUNT windows active"
    else
        check "Windows" "warn" "Only $WINDOW_COUNT windows (expected 6)"
    fi
else
    check "Session" "fail" "Not running"
fi

echo ""
echo -e "${CYAN}[3/8] Files and Directories${NC}"
echo ""

# Check main script
if [ -f "$SCRIPT_DIR/deepseek_orchestrator.py" ]; then
    check "Orchestrator" "pass" "deepseek_orchestrator.py exists"
else
    check "Orchestrator" "fail" "deepseek_orchestrator.py not found"
fi

# Check config
if [ -f "$SCRIPT_DIR/config.json" ]; then
    check "Config" "pass" "config.json exists"
    
    # Validate JSON
    if $PYTHON_CMD -c "import json; json.load(open('config.json'))" 2>/dev/null; then
        check "Config Syntax" "pass" "Valid JSON"
    else
        check "Config Syntax" "fail" "Invalid JSON"
    fi
else
    check "Config" "fail" "config.json not found"
fi

# Check triggers directory
if [ -d "$SCRIPT_DIR/triggers" ]; then
    PENDING=$(ls "$SCRIPT_DIR/triggers"/*.task 2>/dev/null | wc -l)
    RESULTS=$(ls "$SCRIPT_DIR/triggers"/*.result 2>/dev/null | wc -l)
    check "Triggers Dir" "pass" "Exists ($PENDING pending, $RESULTS results)"
else
    check "Triggers Dir" "warn" "Not found (will be created)"
fi

echo ""
echo -e "${CYAN}[4/8] Logs and Database${NC}"
echo ""

# Check orchestrator log
if [ -f "$SCRIPT_DIR/deepseek_orchestrator.log" ]; then
    LOG_SIZE=$(du -h "$SCRIPT_DIR/deepseek_orchestrator.log" | cut -f1)
    LOG_AGE=$(( $(date +%s) - $(stat -c %Y "$SCRIPT_DIR/deepseek_orchestrator.log" 2>/dev/null || stat -f %m "$SCRIPT_DIR/deepseek_orchestrator.log" 2>/dev/null || echo 0) ))
    
    if [ $LOG_AGE -lt 300 ]; then
        check "Orchestrator Log" "pass" "Active ($LOG_SIZE, updated ${LOG_AGE}s ago)"
    else
        check "Orchestrator Log" "warn" "Idle ($LOG_SIZE, updated ${LOG_AGE}s ago)"
    fi
else
    check "Orchestrator Log" "warn" "Not created yet"
fi

# Check audit database
if [ -f "$SCRIPT_DIR/deepseek_audit.db" ]; then
    DB_SIZE=$(du -h "$SCRIPT_DIR/deepseek_audit.db" | cut -f1)
    
    # Count records
    if command -v sqlite3 &> /dev/null; then
        RECORD_COUNT=$(sqlite3 "$SCRIPT_DIR/deepseek_audit.db" "SELECT COUNT(*) FROM audit_log" 2>/dev/null || echo "0")
        check "Audit Database" "pass" "$DB_SIZE, $RECORD_COUNT records"
    else
        check "Audit Database" "pass" "$DB_SIZE"
    fi
else
    check "Audit Database" "warn" "Not created yet"
fi

echo ""
echo -e "${CYAN}[5/8] Python Modules${NC}"
echo ""

# Check watchdog
if $PYTHON_CMD -c "import watchdog" 2>/dev/null; then
    check "watchdog" "pass" "Installed"
else
    check "watchdog" "warn" "Not installed (file watching limited)"
fi

# Check llama-cpp-python
if $PYTHON_CMD -c "import llama_cpp" 2>/dev/null; then
    check "llama-cpp-python" "pass" "Installed (real inference available)"
else
    check "llama-cpp-python" "warn" "Not installed (mock mode only)"
fi

# Check flask
if $PYTHON_CMD -c "import flask" 2>/dev/null; then
    check "flask" "pass" "Installed (web API available)"
else
    check "flask" "warn" "Not installed (web API unavailable)"
fi

echo ""
echo -e "${CYAN}[6/8] Configuration${NC}"
echo ""

if [ -f "$SCRIPT_DIR/config.json" ]; then
    # Check execution mode
    EXEC_MODE=$($PYTHON_CMD -c "import json; print(json.load(open('config.json')).get('execution_mode', 'unknown'))" 2>/dev/null)
    if [ "$EXEC_MODE" = "prompt" ]; then
        check "Execution Mode" "pass" "prompt (safest)"
    elif [ "$EXEC_MODE" = "dry_run" ]; then
        check "Execution Mode" "warn" "dry_run (simulation only)"
    elif [ "$EXEC_MODE" = "auto_approve" ]; then
        check "Execution Mode" "warn" "auto_approve (ensure whitelist is strict)"
    else
        check "Execution Mode" "pass" "$EXEC_MODE"
    fi
    
    # Check model path
    MODEL_PATH=$($PYTHON_CMD -c "import json; print(json.load(open('config.json')).get('model_path', 'null'))" 2>/dev/null)
    if [ "$MODEL_PATH" = "null" ] || [ "$MODEL_PATH" = "None" ]; then
        check "Model Path" "warn" "Not set (mock mode)"
    elif [ -f "$MODEL_PATH" ]; then
        MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
        check "Model Path" "pass" "Valid ($MODEL_SIZE)"
    else
        check "Model Path" "fail" "File not found: $MODEL_PATH"
    fi
fi

echo ""
echo -e "${CYAN}[7/8] Network Services${NC}"
echo ""

# Check if web API port is in use
WEB_PORT=$($PYTHON_CMD -c "import json; print(json.load(open('config.json')).get('web_api', {}).get('port', 5000))" 2>/dev/null)
if command -v netstat &> /dev/null; then
    if netstat -tuln 2>/dev/null | grep -q ":$WEB_PORT "; then
        check "Web API Port" "pass" "Port $WEB_PORT is listening"
    else
        check "Web API Port" "warn" "Port $WEB_PORT not listening (API may not be running)"
    fi
else
    check "netstat" "warn" "Not available (cannot check ports)"
fi

echo ""
echo -e "${CYAN}[8/8] Permissions${NC}"
echo ""

# Check script permissions
SCRIPTS=("deepseek_orchestrator.py" "launch.sh" "service_manager.sh" "voice_command.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "$SCRIPT_DIR/$script" ]; then
        if [ -x "$SCRIPT_DIR/$script" ]; then
            check "$script" "pass" "Executable"
        else
            check "$script" "warn" "Not executable (run: chmod +x $script)"
        fi
    fi
done

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                    Summary                                 ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Passed:${NC}  $PASS"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo -e "${RED}Failed:${NC}  $FAIL"
echo ""

if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System is healthy.${NC}"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo -e "${YELLOW}⚠ System is operational with warnings.${NC}"
    exit 0
else
    echo -e "${RED}✗ Critical issues detected. Please fix failed checks.${NC}"
    exit 1
fi
