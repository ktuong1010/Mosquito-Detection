# Installation Guide

This guide will help you set up and run the Mosquito Detection System on Raspberry Pi.

## Prerequisites

### For Development/Training Machine

- Python 3.8 or higher
- pip package manager
- Git (for cloning repository)
- At least 4GB RAM (recommended for training)

### For Raspberry Pi Deployment

- Raspberry Pi 4 Model B (2GB RAM minimum)
- Raspberry Pi OS (Bullseye or newer)
- Raspberry Pi Camera Module 3 (CSI connection)
- MicroSD card (16GB minimum, 32GB recommended)
- Power supply (5V 3A recommended)
- Optional: SSD1306 OLED display (128x64, I2C)

## Installation Steps

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd MosquitoDetection
```

### Step 2: Install Python Dependencies

#### On Development Machine

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### On Raspberry Pi

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dev
sudo apt-get install -y libatlas-base-dev libopenblas-dev
sudo apt-get install -y libjpeg-dev zlib1g-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements_rpi.txt
```

### Step 3: Enable Raspberry Pi Camera

1. Enable camera using raspi-config:

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **Camera** → **Enable**

Or use command line:

```bash
sudo raspi-config nonint do_camera 0
```

2. Reboot Raspberry Pi:

```bash
sudo reboot
```

3. Verify camera is detected:

```bash
vcgencmd get_camera
```

Should show: `supported=1 detected=1`

See `docs/ENABLE_CAMERA.md` for detailed instructions.

### Step 4: Configure System

Edit `config.py` if needed:

```python
USE_PI_CAMERA = True  # Use Raspberry Pi Camera Module 3
PI_CAMERA_WIDTH = 640
PI_CAMERA_HEIGHT = 480
PI_CAMERA_TARGET_FPS = 10
CONFIDENCE_THRESHOLD = 0.7
```

### Step 5: Test Camera

Run demo script to test camera:

```bash
python3 scripts/demo.py
```

If successful, you should see camera frames and detection results.

### Step 6: Run System

**Demo mode:**

```bash
python3 scripts/demo.py
```

**Full system:**

```bash
python3 main.py
```

The system will start detecting mosquitoes and logging results to the database.

## Model Setup

### Using Provided Model

The project includes a pre-trained model. Ensure the model file is in `models/` directory:

```bash
ls models/*.tflite
```

### Training Your Own Model

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

3. The trained model will be saved in `models/model.tflite`

## Auto-Start on Boot (Raspberry Pi)

To automatically start the system when Raspberry Pi boots:

```bash
cd scripts
chmod +x enable_demo_autostart.sh
./enable_demo_autostart.sh
```

## Verification

### Check System Status

If running as a service:

```bash
sudo systemctl status mosquito-demo.service
```

### View Logs

```bash
# Service logs
sudo journalctl -u mosquito-demo.service -f

# Or if running manually, check:
tail -f logs/detection.log
```

### Test Database

```bash
python3 -c "from src.database import Database; from pathlib import Path; db = Database(Path('data/detections.db')); print('Database OK')"
```

## Troubleshooting

### Camera Not Detected

1. Check CSI ribbon cable connection
2. Verify camera is enabled: `vcgencmd get_camera`
3. Check permissions: `groups $USER`
4. See `docs/CAMERA_TROUBLESHOOTING.md` for detailed help

### Import Errors

1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements_rpi.txt`
3. Check Python version: `python3 --version` (should be 3.8+)

### Model Not Found

1. Verify model file exists: `ls models/*.tflite`
2. Check `MODEL_PATH` in `config.py`
3. Ensure file permissions are correct

### Low Performance

1. Check CPU temperature: `vcgencmd measure_temp`
2. Ensure adequate power supply
3. Close unnecessary applications
4. Check system resources: `htop`

For more troubleshooting, see `docs/TROUBLESHOOTING.md`.

## Next Steps

- Review `README.md` for system overview
- Check `docs/` directory for detailed documentation
- Run `scripts/start_dashboard.py` to start web dashboard
- Explore `config.py` to customize system behavior

## Support

For issues or questions:
1. Check `docs/TROUBLESHOOTING.md`
2. Review GitHub issues
3. Contact project maintainers
