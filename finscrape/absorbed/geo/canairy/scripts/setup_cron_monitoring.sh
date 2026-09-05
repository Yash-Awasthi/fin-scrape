#!/bin/bash

# Non-interactive setup script for cron-based monitoring
# Sets up hourly monitoring checks

echo "🏠 Setting up automated hourly monitoring via cron..."

# Get the current directory
MONITOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PYTHON="$MONITOR_DIR/venv/bin/python"
MAIN_SCRIPT="$MONITOR_DIR/src/main.py"

# Create logs directory if it doesn't exist
mkdir -p "$MONITOR_DIR/logs"

# Create the cron command
CRON_SCHEDULE="0 * * * *"  # Every hour
CRON_CMD="$CRON_SCHEDULE cd $MONITOR_DIR && $VENV_PYTHON $MAIN_SCRIPT --check-status >> $MONITOR_DIR/logs/cron.log 2>&1"

echo "📝 Adding cron job to run every hour..."

# Add to crontab
(crontab -l 2>/dev/null | grep -v "household-resilience-monitor"; echo "# Household Resilience Monitoring - every hour"; echo "$CRON_CMD") | crontab -

echo "✅ Cron job installed!"
echo ""
echo "Monitoring will run automatically every hour."
echo ""
echo "Useful commands:"
echo "- View cron jobs: crontab -l"
echo "- View logs: tail -f $MONITOR_DIR/logs/cron.log"
echo "- Remove cron job: crontab -e (then delete the lines)"
echo "- Test immediately: cd $MONITOR_DIR && ./venv/bin/python src/main.py --check-status"
echo ""
echo "🎉 Automated monitoring setup complete!"