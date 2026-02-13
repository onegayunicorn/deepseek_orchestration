#!/data/data/com.termux/files/usr/bin/bash
# DeepSeek Orchestrator - Automated Database Backup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKUP_DIR="$BASE_DIR/data/backups"
DB_FILE="$BASE_DIR/deepseek_audit.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_DIR/audit_backup_$TIMESTAMP.db"
    # Keep only last 30 days of backups
    find "$BACKUP_DIR" -name "*.db" -type f -mtime +30 -delete
    echo "Backup completed: audit_backup_$TIMESTAMP.db"
else
    echo "Database file not found at $DB_FILE"
fi
