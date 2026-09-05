#!/bin/bash

# Start the Household Resilience Web Dashboard

echo "🌐 Starting Household Resilience Dashboard..."
echo "============================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Set Flask environment variables
export FLASK_APP="$SCRIPT_DIR/app.py"
export FLASK_ENV="production"

# Change to dashboard directory
cd "$SCRIPT_DIR"

echo ""
echo "📍 Dashboard will be available at:"
echo "   Local: http://localhost:5555"
echo "   Network: http://$(hostname):5555"
echo ""
echo "📱 Family members on the same network can access using the Network URL"
echo ""
echo "Press Ctrl+C to stop the dashboard"
echo "============================================"
echo ""

# Run the Flask app
python app.py