#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Continuous Voice Listener
# Continuously listens for voice commands in a loop
#

# Configuration
COOLDOWN_SECONDS=3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🎤 Continuous Voice Listener${NC}"
echo -e "${CYAN}=============================${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Counter for commands processed
COMMAND_COUNT=0

while true; do
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] Listening...${NC}"
    
    # Run the voice command script
    if bash "$SCRIPT_DIR/voice_command.sh"; then
        COMMAND_COUNT=$((COMMAND_COUNT + 1))
        echo -e "${GREEN}Commands processed: $COMMAND_COUNT${NC}"
    fi
    
    # Cooldown period to prevent rapid re-triggering
    echo ""
    echo -e "${CYAN}Cooldown: ${COOLDOWN_SECONDS}s${NC}"
    sleep "$COOLDOWN_SECONDS"
    echo ""
done
