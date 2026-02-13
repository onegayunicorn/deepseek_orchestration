#!/data/data/com.termux/files/usr/bin/bash
#
# DeepSeek Orchestrator - Auto-Start Script
# Place in ~/.termux/boot/ to start services automatically
#

# Wait for Termux to fully initialize
sleep 10

# Change to orchestrator directory
cd ~/deepseek_orchestration || exit 1

# Start services using service manager
bash service_manager.sh start

# Optional: Send notification
if command -v termux-notification &> /dev/null; then
    termux-notification \
        --title "DeepSeek Orchestrator" \
        --content "Services started automatically" \
        --icon "🦅"
fi
