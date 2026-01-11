#!/bin/bash
# Setup script for Raspberry Pi deployment
# Automatically installs dependencies and configures system

set -e

echo "=========================================="
echo "Mosquito Detection System - Setup"
echo "=========================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Project directory: $PROJECT_DIR"

# Update system
echo ""
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo ""
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libopenexr-dev \
    libgstreamer1.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk-3-dev \
    libtiff5-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libv4l-dev \
    v4l-utils \
    i2c-tools \
    git

# Enable I2C for OLED
echo ""
echo "Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Enable camera
echo ""
echo "Enabling camera interface..."
# Try different methods depending on Raspberry Pi OS version
if sudo raspi-config nonint do_camera 0 2>/dev/null; then
    echo "Camera enabled via raspi-config"
else
    echo "Trying alternative method to enable camera..."
    # For newer Raspberry Pi OS versions
    sudo raspi-config nonint do_legacy 0 2>/dev/null || true
    # Enable camera via config.txt
    if ! grep -q "^camera_auto_detect=1" /boot/firmware/config.txt 2>/dev/null; then
        echo "camera_auto_detect=1" | sudo tee -a /boot/firmware/config.txt > /dev/null 2>&1 || \
        echo "gpu_mem=128" | sudo tee -a /boot/config.txt > /dev/null 2>&1 || true
    fi
    echo "Camera configuration updated. Reboot may be required."
fi

# Install Python packages
echo ""
echo "Installing Python packages..."
pip3 install --upgrade pip setuptools wheel

# Install TensorFlow Lite Runtime
echo ""
echo "Installing TensorFlow Lite Runtime..."
ARCH=$(uname -m)
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}{sys.version_info.minor}')")
echo "Detected architecture: $ARCH, Python: $PYTHON_VERSION"

if [ "$ARCH" = "armv7l" ]; then
    echo "Installing TensorFlow for ARM (full version, includes newer TFLite runtime)..."
    echo "Note: This may take 10-15 minutes and requires ~500MB disk space"
    pip3 install --upgrade tensorflow==2.13.0 || \
    pip3 install --upgrade "tensorflow>=2.10.0,<2.14.0" || \
    pip3 install tensorflow
else
    echo "Installing TensorFlow Lite..."
    pip3 install --upgrade tensorflow-lite>=2.13.0 || \
    pip3 install tensorflow-lite
fi

# Install requirements
echo ""
echo "Installing project requirements..."
if [ -f "requirements_rpi.txt" ]; then
    pip3 install -r requirements_rpi.txt
else
    pip3 install -r requirements.txt
fi

# Create directories
echo ""
echo "Creating directories..."
mkdir -p logs
mkdir -p models
mkdir -p data

# Check model
MODEL_FILE="models/model.tflite"
if [ ! -f "$MODEL_FILE" ]; then
    echo ""
    echo "WARNING: Model file not found"
    echo "Expected: $MODEL_FILE"
    echo "Please copy your trained model to this location."
else
    echo ""
    echo "Model file found: $MODEL_FILE"
fi

# Setup database
echo ""
echo "Setting up database..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '.')
from src.database import Database
db = Database(Path('data/detections.db'))
print('Database initialized')
" || echo "Warning: Could not initialize database (may need to run manually)"

# Install systemd service
echo ""
echo "Installing systemd service..."
sudo cp deployment/mosquito-detection.service /etc/systemd/system/
sudo systemctl daemon-reload

# Update service file with correct paths
USER_NAME=$(whoami)
HOME_DIR=$(eval echo ~$USER_NAME)
PROJECT_DIR_ABS=$(cd "$PROJECT_DIR" && pwd)

# Update service file with actual paths
sudo sed -i "s|User=pi|User=$USER_NAME|g" /etc/systemd/system/mosquito-detection.service
sudo sed -i "s|/home/pi/MosquitoDetection|$PROJECT_DIR_ABS|g" /etc/systemd/system/mosquito-detection.service

# Reload after update
sudo systemctl daemon-reload

echo ""
echo "=========================================="
echo "Setup completed!"
echo "=========================================="
echo ""
echo "Service installed. Options:"
echo ""
echo "1. Enable auto-start (recommended):"
echo "   sudo systemctl enable mosquito-detection.service"
echo "   sudo systemctl start mosquito-detection.service"
echo ""
echo "2. Test manually first:"
echo "   python3 main.py"
echo ""
echo "3. Check service status:"
echo "   sudo systemctl status mosquito-detection.service"
echo ""
read -p "Do you want to enable auto-start now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo systemctl enable mosquito-detection.service
    echo "Service enabled for auto-start on boot."
    read -p "Do you want to start the service now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start mosquito-detection.service
        echo "Service started. Check status with: sudo systemctl status mosquito-detection.service"
    fi
else
    echo "Service not enabled. Enable later with: sudo systemctl enable mosquito-detection.service"
fi
echo ""


