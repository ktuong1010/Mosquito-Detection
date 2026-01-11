#!/bin/bash
# Script to enable auto-start for Mosquito Detection Demo

set -e

echo "========================================"
echo "Enable Auto-Start for Mosquito Detection Demo"
echo "========================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

USER_NAME=$(whoami)
HOME_DIR=$(eval echo ~$USER_NAME)
PROJECT_DIR_ABS=$(pwd)

echo "User: $USER_NAME"
echo "Project directory: $PROJECT_DIR_ABS"
echo ""

SERVICE_FILE="deployment/mosquito-demo.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "ERROR: Service file not found: $SERVICE_FILE"
    exit 1
fi

echo "Installing service file..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/

echo "Updating paths in service file..."
sudo sed -i "s|User=khanhtuong|User=$USER_NAME|g" /etc/systemd/system/mosquito-demo.service
sudo sed -i "s|/home/khanhtuong/MosquitoDetection|$PROJECT_DIR_ABS|g" /etc/systemd/system/mosquito-demo.service

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo ""
echo "Enabling auto-start..."
sudo systemctl enable mosquito-demo.service

echo ""
echo "========================================"
echo "Auto-start enabled successfully!"
echo "========================================"
echo ""
echo "Service will start automatically on boot."
echo ""
echo "Commands:"
echo "  Start now:     sudo systemctl start mosquito-demo.service"
echo "  Stop:          sudo systemctl stop mosquito-demo.service"
echo "  Status:        sudo systemctl status mosquito-demo.service"
echo "  View logs:     sudo journalctl -u mosquito-demo.service -f"
echo "  Disable:       sudo systemctl disable mosquito-demo.service"
echo ""

read -p "Do you want to start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting service..."
    sudo systemctl start mosquito-demo.service
    echo ""
    echo "Service started. Checking status..."
    sleep 2
    sudo systemctl status mosquito-demo.service --no-pager -l
fi

echo ""
echo "Done!"

