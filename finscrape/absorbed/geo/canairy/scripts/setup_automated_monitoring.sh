#!/bin/bash

# Automated Monitoring Setup Script for Household Resilience System
# Provides multiple options for scheduling automated checks

echo "🏠 Household Resilience - Automated Monitoring Setup"
echo "===================================================="
echo ""
echo "Choose your monitoring setup method:"
echo "1. Cron (Mac/Linux) - Reliable, runs in background"
echo "2. LaunchAgent (Mac) - Native macOS scheduling"
echo "3. Systemd (Linux) - Modern Linux service"
echo "4. Simple Background Script - Easy to start/stop"
echo ""

# Get the current directory
MONITOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$MONITOR_DIR/venv/bin/python"
MAIN_SCRIPT="$MONITOR_DIR/src/main.py"

# Function to setup cron
setup_cron() {
    echo "📅 Setting up Cron scheduling..."
    echo ""
    echo "Choose monitoring frequency:"
    echo "1. Every hour (recommended)"
    echo "2. Every 30 minutes"
    echo "3. Every 2 hours"
    echo "4. Every 6 hours"
    echo "5. Once daily at 8 AM"
    
    read -p "Select option (1-5): " freq_choice
    
    case $freq_choice in
        1) CRON_SCHEDULE="0 * * * *" ; DESC="every hour" ;;
        2) CRON_SCHEDULE="*/30 * * * *" ; DESC="every 30 minutes" ;;
        3) CRON_SCHEDULE="0 */2 * * *" ; DESC="every 2 hours" ;;
        4) CRON_SCHEDULE="0 */6 * * *" ; DESC="every 6 hours" ;;
        5) CRON_SCHEDULE="0 8 * * *" ; DESC="daily at 8 AM" ;;
        *) CRON_SCHEDULE="0 * * * *" ; DESC="every hour (default)" ;;
    esac
    
    # Create the cron command
    CRON_CMD="$CRON_SCHEDULE cd $MONITOR_DIR && $VENV_PYTHON $MAIN_SCRIPT --check-status >> $MONITOR_DIR/logs/cron.log 2>&1"
    
    echo ""
    echo "📝 Adding cron job to run $DESC..."
    
    # Add to crontab
    (crontab -l 2>/dev/null | grep -v "household-resilience-monitor"; echo "# Household Resilience Monitoring - $DESC"; echo "$CRON_CMD") | crontab -
    
    echo "✅ Cron job installed!"
    echo ""
    echo "To view your cron jobs: crontab -l"
    echo "To remove: crontab -e (then delete the lines)"
    echo "Logs will be in: $MONITOR_DIR/logs/cron.log"
}

# Function to setup LaunchAgent (macOS)
setup_launchagent() {
    echo "🍎 Setting up macOS LaunchAgent..."
    
    PLIST_FILE="$HOME/Library/LaunchAgents/com.household.resilience.monitor.plist"
    
    cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.household.resilience.monitor</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$MAIN_SCRIPT</string>
        <string>--check-status</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$MONITOR_DIR</string>
    
    <key>StartInterval</key>
    <integer>3600</integer> <!-- Run every hour (3600 seconds) -->
    
    <key>StandardOutPath</key>
    <string>$MONITOR_DIR/logs/launchagent.log</string>
    
    <key>StandardErrorPath</key>
    <string>$MONITOR_DIR/logs/launchagent_error.log</string>
    
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF
    
    # Load the agent
    launchctl load "$PLIST_FILE"
    
    echo "✅ LaunchAgent installed and started!"
    echo ""
    echo "To check status: launchctl list | grep resilience"
    echo "To stop: launchctl unload $PLIST_FILE"
    echo "To start: launchctl load $PLIST_FILE"
}

# Function to setup systemd (Linux)
setup_systemd() {
    echo "🐧 Setting up systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/household-resilience.service"
    TIMER_FILE="/etc/systemd/system/household-resilience.timer"
    
    # Create service file
    sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Household Resilience Monitoring System
After=network.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$MONITOR_DIR
ExecStart=$VENV_PYTHON $MAIN_SCRIPT --check-status
StandardOutput=append:$MONITOR_DIR/logs/systemd.log
StandardError=append:$MONITOR_DIR/logs/systemd_error.log

[Install]
WantedBy=multi-user.target
EOF

    # Create timer file
    sudo tee "$TIMER_FILE" > /dev/null << EOF
[Unit]
Description=Run Household Resilience Monitor every hour
Requires=household-resilience.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable and start
    sudo systemctl daemon-reload
    sudo systemctl enable household-resilience.timer
    sudo systemctl start household-resilience.timer
    
    echo "✅ Systemd timer installed and started!"
    echo ""
    echo "To check status: systemctl status household-resilience.timer"
    echo "To view logs: journalctl -u household-resilience"
}

# Function to create simple background script
setup_background() {
    echo "📜 Creating background monitoring script..."
    
    MONITOR_SCRIPT="$MONITOR_DIR/run_monitor.sh"
    
    cat > "$MONITOR_SCRIPT" << 'EOF'
#!/bin/bash
# Simple monitoring loop - runs until stopped

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
MAIN_SCRIPT="$SCRIPT_DIR/src/main.py"
PID_FILE="$SCRIPT_DIR/monitor.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Monitor already running with PID $OLD_PID"
        exit 1
    fi
fi

# Save PID
echo $$ > "$PID_FILE"

echo "🏃 Starting Household Resilience Monitor"
echo "PID: $$"
echo "Monitoring every hour. Press Ctrl+C to stop."
echo "Logs: $SCRIPT_DIR/logs/monitor.log"
echo ""

# Trap to clean up on exit
trap "rm -f $PID_FILE; echo 'Monitor stopped'; exit" INT TERM

# Run monitoring loop
while true; do
    echo "[$(date)] Running status check..."
    cd "$SCRIPT_DIR" && "$VENV_PYTHON" "$MAIN_SCRIPT" --check-status
    
    # Sleep for 1 hour
    sleep 3600
done
EOF

    chmod +x "$MONITOR_SCRIPT"
    
    # Create stop script
    STOP_SCRIPT="$MONITOR_DIR/stop_monitor.sh"
    cat > "$STOP_SCRIPT" << 'EOF'
#!/bin/bash
# Stop the monitoring script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/monitor.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Stopping monitor (PID: $PID)..."
        kill "$PID"
        rm -f "$PID_FILE"
        echo "✅ Monitor stopped"
    else
        echo "Monitor not running (stale PID file)"
        rm -f "$PID_FILE"
    fi
else
    echo "Monitor not running (no PID file)"
fi
EOF

    chmod +x "$STOP_SCRIPT"
    
    echo "✅ Background scripts created!"
    echo ""
    echo "To start: ./run_monitor.sh &"
    echo "To stop: ./stop_monitor.sh"
    echo "To run in background: nohup ./run_monitor.sh > /dev/null 2>&1 &"
}

# Main menu
echo "Select setup method:"
read -p "Enter choice (1-4): " choice

case $choice in
    1) setup_cron ;;
    2) setup_launchagent ;;
    3) setup_systemd ;;
    4) setup_background ;;
    *) echo "Invalid choice. Exiting." ; exit 1 ;;
esac

echo ""
echo "🎉 Automated monitoring setup complete!"
echo ""
echo "Additional commands:"
echo "- Check current status manually: cd $MONITOR_DIR && ./venv/bin/python src/main.py --check-status"
echo "- View logs: tail -f $MONITOR_DIR/logs/monitor.log"
echo "- Test configuration: cd $MONITOR_DIR && ./venv/bin/python scripts/test_credentials.py"
echo ""
echo "The system will now monitor your trip-wire indicators automatically!"