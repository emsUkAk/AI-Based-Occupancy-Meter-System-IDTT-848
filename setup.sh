#!/bin/bash

# Setup script for Occupancy Meter System

echo "=========================================="
echo "Occupancy Meter System - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip first."
    exit 1
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Check if MQTT broker is running (optional)
echo ""
echo "Checking MQTT broker..."
if command -v mosquitto &> /dev/null; then
    echo "✓ Mosquitto is installed"
    echo "  To start MQTT broker: mosquitto -v"
else
    echo "⚠️  Mosquitto not found. You may need to install an MQTT broker."
    echo "  Install: brew install mosquitto (macOS) or apt-get install mosquitto (Linux)"
fi

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your settings"
echo "2. Start MQTT broker (if not running): mosquitto -v"
echo "3. Run the system: python3 occupancy_detector.py"
echo "4. Test MQTT messages: python3 mqtt_test_client.py"
echo ""

