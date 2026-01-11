# Mosquito Detection System

A TinyML-based real-time mosquito species classification system for Raspberry Pi using Raspberry Pi Camera Module 3 and TensorFlow Lite.

## Overview

This system performs real-time classification of mosquito species (Aedes and Culex) using a MobileNetV2-based TensorFlow Lite model. The system is optimized for deployment on Raspberry Pi 4 Model B with Raspberry Pi Camera Module 3 (CSI).

## Features

- Real-time mosquito species classification (Aedes, Culex)
- Raspberry Pi Camera Module 3 (CSI) integration
- TensorFlow Lite model for efficient inference
- SQLite database for detection logging
- OLED display for real-time results
- Web dashboard for data visualization
- Automatic startup on Raspberry Pi boot
- Performance monitoring (FPS, latency tracking)

## Quick Deploy

**For detailed deployment instructions, see [DEPLOY.md](DEPLOY.md)**

### Quick Start (Windows)

Open PowerShell in the `MosquitoDetection` directory:

```powershell
.\deployment\deploy_from_windows.ps1 -RpiHost khanhtuong@raspberrypi.local
```

**Note:** Use `.\` to run the script, not `cd`.

### Quick Start (Linux/Mac)

```bash
cd MosquitoDetection
./deployment/deploy.sh khanhtuong@raspberrypi.local
```

Replace `khanhtuong@raspberrypi.local` with your Raspberry Pi username and hostname.

## System Requirements

### Hardware
- Raspberry Pi 4 Model B (2GB RAM minimum)
- Raspberry Pi Camera Module 3 (CSI connection)
- Optional: SSD1306 OLED display (128x64, I2C)

### Software
- Raspberry Pi OS (Bullseye or newer)
- Python 3.8 or higher

## Project Structure

```
MosquitoDetection/
├── config.py                 # System configuration
├── main.py                   # Main entry point
├── requirements.txt          # Python dependencies
├── requirements_rpi.txt      # Raspberry Pi specific dependencies
│
├── src/                      # Source code
│   ├── pi_camera.py         # Raspberry Pi Camera interface
│   ├── preprocessing.py     # Image preprocessing
│   ├── model.py             # TensorFlow Lite inference
│   ├── oled_display.py      # OLED display
│   ├── display.py           # Display interface
│   ├── database.py          # SQLite database logging
│   ├── visualization.py    # Data visualization
│   └── dashboard.py         # Web dashboard
│
├── deployment/              # Deployment scripts
│   ├── setup.sh            # Raspberry Pi setup script
│   ├── deploy.sh           # Deployment automation
│   └── mosquito-demo.service  # Systemd service
│
├── scripts/                 # Utility scripts
│   ├── demo.py             # Demo script
│   ├── start_dashboard.py  # Start web dashboard
│   ├── train_mobilenetv2.py  # Model training script
│   └── convert_model_compatible.py  # Model conversion
│
├── models/                  # Model files
│   └── model.tflite        # TensorFlow Lite model
│
├── data/                    # Data directory
│   └── detections.db       # SQLite database
│
└── docs/                    # Documentation
    ├── INSTALLATION.md     # Installation guide
    ├── DEPLOY.md           # Deployment guide
    └── DASHBOARD.md        # Dashboard guide
```

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd MosquitoDetection
```

### 2. Install Dependencies

On Raspberry Pi:

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev
sudo apt-get install -y libatlas-base-dev libopenblas-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements_rpi.txt
```

On development machine (for training):

```bash
pip install -r requirements.txt
```

### 3. Enable Camera

Enable Raspberry Pi Camera Module 3:

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **Camera** → **Enable**

Or use command line:

```bash
sudo raspi-config nonint do_camera 0
```

Reboot after enabling:

```bash
sudo reboot
```

See `docs/ENABLE_CAMERA.md` for detailed instructions.

### 4. Configure System

Edit `config.py` if needed:

```python
USE_PI_CAMERA = True  # Use Pi Camera Module 3
PI_CAMERA_WIDTH = 640
PI_CAMERA_HEIGHT = 480
PI_CAMERA_TARGET_FPS = 10
CONFIDENCE_THRESHOLD = 0.7
```

### 5. Run System

**Demo mode:**

```bash
python3 scripts/demo.py
```

**Full system:**

```bash
python3 main.py
```

**Auto-start on boot:**

```bash
cd scripts
chmod +x enable_demo_autostart.sh
./enable_demo_autostart.sh
```

## Model Information

The system uses a MobileNetV2-based TensorFlow Lite model:

- Input size: 224x224 RGB
- Output: 2 classes (Aedes, Culex)
- Model size: ~2.5 MB
- Quantization: INT8 for optimal performance

### Using Your Own Model

1. Train model using `scripts/train_mobilenetv2.py`
2. Convert to TFLite format
3. Place model file in `models/` directory
4. Update `MODEL_PATH` in `config.py`

## Web Dashboard

Start the web dashboard to view detection statistics:

```bash
python3 scripts/start_dashboard.py
```

Access dashboard at: `http://<raspberry-pi-ip>:5000`

The dashboard shows:
- Daily and weekly mosquito density charts
- Detection statistics (count, confidence)
- Real-time updates

See `docs/DASHBOARD.md` for detailed instructions.

## Data Visualization

### View Daily Density

```bash
python3 scripts/view_daily_density.py
```

### Generate Plots

```bash
python3 scripts/plot_density.py
```

Plots are saved to `plots/` directory.

## Model Training

### Training on Development Machine

1. Prepare dataset in `dataset/processed_edgeimpulse/`:

```
dataset/processed_edgeimpulse/
├── train/
│   ├── Aedes/
│   └── Culex/
└── val/
    ├── Aedes/
    └── Culex/
```

2. Run training:

```bash
python3 scripts/train_mobilenetv2.py --epochs 30 --convert-tflite
```

3. Transfer model to Raspberry Pi:

```bash
scp models/model.tflite khanhtuong@raspberrypi.local:~/MosquitoDetection/models/
```

See `docs/TRAINING.md` for detailed instructions.

## Service Management

If installed as a service:

```bash
# Start service
sudo systemctl start mosquito-demo.service

# Stop service
sudo systemctl stop mosquito-demo.service

# Enable auto-start on boot
sudo systemctl enable mosquito-demo.service

# Disable auto-start
sudo systemctl disable mosquito-demo.service

# View logs
sudo journalctl -u mosquito-demo.service -f

# Check status
sudo systemctl status mosquito-demo.service
```

## Performance

Expected performance on Raspberry Pi 4:

- Frame rate: 4-5 FPS
- Inference latency: 100-150ms per frame
- Memory usage: ~200-300 MB
- CPU usage: 30-50%

## Troubleshooting

### Camera Not Detected

1. Check camera connection (CSI ribbon cable)
2. Verify camera is enabled: `vcgencmd get_camera`
3. Check camera module: `lsmod | grep bcm2835`
4. See `docs/CAMERA_TROUBLESHOOTING.md` for detailed help

### Model Not Found

1. Verify model file exists: `ls models/*.tflite`
2. Check `MODEL_PATH` in `config.py`
3. Ensure model file has correct permissions

### Low Performance

1. Check CPU temperature: `vcgencmd measure_temp`
2. Ensure adequate power supply (5V 3A recommended)
3. Close unnecessary applications
4. Check system load: `top`

See `docs/TROUBLESHOOTING.md` for more details.

## Documentation

- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [Deployment Guide](DEPLOY.md) - Deployment to Raspberry Pi
- [Dashboard Guide](docs/DASHBOARD.md) - Web dashboard usage
- [Training Guide](docs/TRAINING.md) - Model training documentation
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Development

### Running Tests

```bash
python3 -m pytest tests/
```

### Code Structure

- `src/pi_camera.py`: Raspberry Pi Camera Module 3 interface
- `src/preprocessing.py`: Image preprocessing for model input
- `src/model.py`: TensorFlow Lite model wrapper
- `src/database.py`: SQLite database operations
- `src/oled_display.py`: OLED display interface
- `src/dashboard.py`: Web dashboard Flask application

## License

Academic project - Group 2 CSE2022

## Authors

TinyML Mosquito Detection Team

## Acknowledgments

- TensorFlow Lite for efficient inference
- MobileNetV2 architecture for lightweight classification
- Raspberry Pi Foundation for hardware platform
