#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Voice Command Bridge
# This script captures voice input and creates trigger files for the orchestrator
#

# Configuration
WATCH_DIR="${WATCH_DIR:-./triggers}"
WAKE_WORD="${WAKE_WORD:-orchestrator}"
AUDIO_FILE="/sdcard/voice_temp.wav"
RECORD_DURATION=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create triggers directory if it doesn't exist
mkdir -p "$WATCH_DIR"

echo -e "${YELLOW}🎤 Voice Command Bridge${NC}"
echo -e "${YELLOW}========================${NC}"
echo ""

# Check if termux-api is installed
if ! command -v termux-microphone-record &> /dev/null; then
    echo -e "${RED}Error: Termux:API not installed${NC}"
    echo "Install with: pkg install termux-api"
    echo "Also install the Termux:API app from F-Droid"
    exit 1
fi

# Check for speech-to-text capability
if ! command -v termux-speech-to-text &> /dev/null; then
    echo -e "${RED}Error: Speech-to-text not available${NC}"
    echo "Make sure Termux:API is properly installed"
    exit 1
fi

echo -e "${GREEN}✓ Termux:API detected${NC}"
echo ""

# Record audio
echo -e "${YELLOW}🔴 Recording for ${RECORD_DURATION} seconds...${NC}"
echo "Speak your command now!"
echo ""

termux-microphone-record -d "$RECORD_DURATION" -f "$AUDIO_FILE" 2>/dev/null

if [ ! -f "$AUDIO_FILE" ]; then
    echo -e "${RED}Error: Failed to record audio${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Recording complete${NC}"
echo ""

# Transcribe using Android's native speech recognition
echo -e "${YELLOW}🔄 Transcribing...${NC}"

# Use termux-speech-to-text with the recorded file
TRANSCRIPT=$(termux-speech-to-text 2>/dev/null)

# Clean up audio file
rm -f "$AUDIO_FILE"

if [ -z "$TRANSCRIPT" ]; then
    echo -e "${RED}Error: No speech detected or transcription failed${NC}"
    echo "Try speaking more clearly or check microphone permissions"
    exit 1
fi

echo -e "${GREEN}✓ Transcription complete${NC}"
echo ""
echo -e "${YELLOW}You said:${NC} \"$TRANSCRIPT\""
echo ""

# Wake-word check (case-insensitive)
TRANSCRIPT_LOWER=$(echo "$TRANSCRIPT" | tr '[:upper:]' '[:lower:]')
WAKE_WORD_LOWER=$(echo "$WAKE_WORD" | tr '[:upper:]' '[:lower:]')

if [[ "$TRANSCRIPT_LOWER" =~ ^$WAKE_WORD_LOWER ]]; then
    # Remove wake word from the beginning
    CLEAN_CMD=$(echo "$TRANSCRIPT" | sed -E "s/^$WAKE_WORD //i" | sed -E "s/^$WAKE_WORD_LOWER //i")
    
    echo -e "${GREEN}✓ Wake word detected${NC}"
    echo -e "${YELLOW}Command:${NC} \"$CLEAN_CMD\""
    echo ""
    
    # Create task file with timestamp
    TASK_FILE="$WATCH_DIR/voice_$(date +%Y%m%d_%H%M%S).task"
    echo "$CLEAN_CMD" > "$TASK_FILE"
    
    echo -e "${GREEN}✓ Task queued: $TASK_FILE${NC}"
    echo ""
    echo "The orchestrator will process this command."
    
    # Optional: Show a notification
    if command -v termux-notification &> /dev/null; then
        termux-notification --title "Voice Command" --content "Processing: $CLEAN_CMD"
    fi
    
else
    echo -e "${RED}✗ Wake word '$WAKE_WORD' not detected${NC}"
    echo "Your command must start with '$WAKE_WORD'"
    echo ""
    echo "Example: '$WAKE_WORD show disk space'"
    exit 1
fi

echo -e "${GREEN}Done!${NC}"
