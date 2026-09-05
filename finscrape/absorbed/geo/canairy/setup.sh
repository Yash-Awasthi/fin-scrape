#!/bin/bash
# Setup script for Household Resilience Monitor

echo "==================================="
echo "Household Resilience Monitor Setup"
echo "==================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p data/{raw,processed,historical,exports}
mkdir -p alerts
mkdir -p config
echo "✓ Directories created"

# Copy secrets template if needed
if [ ! -f "config/secrets.yaml" ] && [ -f "config/secrets.yaml.template" ]; then
    echo "Creating secrets.yaml from template..."
    cp config/secrets.yaml.template config/secrets.yaml
    echo "✓ Secrets file created - please edit config/secrets.yaml with your credentials"
fi

# Run import test
echo ""
echo "Testing imports..."
python test_imports.py

echo ""
echo "==================================="
echo "Setup complete!"
echo "==================================="
echo ""
echo "To run the monitor:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run status check: python src/main.py --check-status"
echo "  3. Run continuous monitoring: python src/main.py"
echo ""
echo "Configuration:"
echo "  - Edit config/config.yaml for thresholds and settings"
echo "  - Edit config/secrets.yaml for API keys and credentials"
echo ""