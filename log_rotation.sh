#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Log Rotation Script
# Automatically rotate and clean old logs
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
LOG_DIR="$SCRIPT_DIR"
RETENTION_DAYS=14
ARCHIVE_DIR="$SCRIPT_DIR/logs_archive"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}DeepSeek Orchestrator - Log Rotation${NC}"
echo "Retention: $RETENTION_DAYS days"
echo ""

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Find and archive logs older than retention period
OLD_LOGS=$(find "$LOG_DIR" -maxdepth 1 -name "*.log" -type f -mtime +$RETENTION_DAYS 2>/dev/null)

if [ -n "$OLD_LOGS" ]; then
    echo -e "${YELLOW}Archiving old logs...${NC}"
    
    for log in $OLD_LOGS; do
        filename=$(basename "$log")
        archive_name="${filename%.log}_$(date +%Y%m%d_%H%M%S).log.gz"
        
        echo "  Archiving: $filename -> $archive_name"
        gzip -c "$log" > "$ARCHIVE_DIR/$archive_name"
        
        if [ $? -eq 0 ]; then
            rm "$log"
            echo "  ✓ Archived and removed"
        else
            echo "  ✗ Failed to archive"
        fi
    done
else
    echo "No logs older than $RETENTION_DAYS days found"
fi

# Clean very old archives (older than 90 days)
echo ""
echo -e "${YELLOW}Cleaning old archives...${NC}"
OLD_ARCHIVES=$(find "$ARCHIVE_DIR" -name "*.log.gz" -type f -mtime +90 2>/dev/null)

if [ -n "$OLD_ARCHIVES" ]; then
    for archive in $OLD_ARCHIVES; do
        filename=$(basename "$archive")
        echo "  Removing: $filename"
        rm "$archive"
    done
else
    echo "No archives older than 90 days found"
fi

# Rotate current log if it's too large (> 10MB)
CURRENT_LOG="$LOG_DIR/deepseek_orchestrator.log"
if [ -f "$CURRENT_LOG" ]; then
    SIZE=$(stat -c%s "$CURRENT_LOG" 2>/dev/null || stat -f%z "$CURRENT_LOG" 2>/dev/null || echo 0)
    SIZE_MB=$((SIZE / 1024 / 1024))
    
    if [ $SIZE_MB -gt 10 ]; then
        echo ""
        echo -e "${YELLOW}Current log is ${SIZE_MB}MB, rotating...${NC}"
        
        archive_name="deepseek_orchestrator_$(date +%Y%m%d_%H%M%S).log.gz"
        gzip -c "$CURRENT_LOG" > "$ARCHIVE_DIR/$archive_name"
        
        if [ $? -eq 0 ]; then
            > "$CURRENT_LOG"  # Truncate the file
            echo "✓ Log rotated successfully"
        else
            echo "✗ Failed to rotate log"
        fi
    fi
fi

echo ""
echo -e "${GREEN}Log rotation complete${NC}"

# Show summary
echo ""
echo "Summary:"
echo "  Active logs: $(find "$LOG_DIR" -maxdepth 1 -name "*.log" -type f | wc -l)"
echo "  Archived logs: $(find "$ARCHIVE_DIR" -name "*.log.gz" -type f | wc -l)"
echo "  Archive size: $(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)"
