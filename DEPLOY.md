# Deployment Guide - Mosquito Detection System

Quick guide to deploy the Mosquito Detection System to Raspberry Pi.

## Prerequisites

1. **Raspberry Pi 4** with Raspberry Pi OS installed
2. **Raspberry Pi Camera Module 3** (CSI connection)
3. **SSH access** to Raspberry Pi (enabled by default on newer OS)
4. **Network connection** between your computer and Raspberry Pi

## Step 1: Enable Camera on Raspberry Pi

1. SSH into Raspberry Pi:

```bash
ssh khanhtuong@raspberrypi.local
```

2. Enable camera:

```bash
sudo raspi-config
```

Navigate to: **Interface Options** → **Camera** → **Enable**

Or use command line:

```bash
sudo raspi-config nonint do_camera 0
```

3. Reboot:

```bash
sudo reboot
```

4. Verify camera is detected:

```bash
vcgencmd get_camera
```

Should show: `supported=1 detected=1`

See `docs/ENABLE_CAMERA.md` for detailed instructions.

## Step 2: Deploy to Raspberry Pi

### Option A: Deploy from Windows (PowerShell)

Open PowerShell in the `MosquitoDetection` directory and run:

```powershell
.\deployment\deploy_from_windows.ps1 -RpiHost khanhtuong@raspberrypi.local
```

Or if you're in a different directory:

```powershell
cd D:\Python\TinyML_MosquitoDetection\MosquitoDetection
.\deployment\deploy_from_windows.ps1 -RpiHost khanhtuong@raspberrypi.local
```

**Note:** Use `.\` to run the script, not `cd`. Replace `khanhtuong@raspberrypi.local` with your Raspberry Pi username and hostname.

### Option B: Deploy from Linux/Mac (Bash)

```bash
cd MosquitoDetection
./deployment/deploy.sh khanhtuong@raspberrypi.local
```

### Option C: Manual Deployment

1. **Copy model file** (if not already on Raspberry Pi):

```bash
scp models/model.tflite khanhtuong@raspberrypi.local:~/MosquitoDetection/models/
```

2. **Copy project files**:

```bash
scp -r src scripts deployment config.py main.py requirements_rpi.txt khanhtuong@raspberrypi.local:~/MosquitoDetection/
```

3. **SSH into Raspberry Pi**:

```bash
ssh khanhtuong@raspberrypi.local
```

4. **Run setup script**:

```bash
cd ~/MosquitoDetection
chmod +x deployment/setup.sh
./deployment/setup.sh
```

## Step 3: Test the System

```bash
cd ~/MosquitoDetection
python3 scripts/demo.py
```

You should see:
- Camera initialization messages
- Frame capture and processing
- Detection results in console
- OLED display updates (if connected)

Press `Ctrl+C` to stop.

## Step 4: Enable Auto-Start (Optional)

To start the system automatically on boot:

```bash
cd ~/MosquitoDetection/scripts
chmod +x enable_demo_autostart.sh
./enable_demo_autostart.sh
```

Check status:

```bash
sudo systemctl status mosquito-demo.service
```

View logs:

```bash
journalctl -u mosquito-demo.service -f
```

## Step 5: Start Web Dashboard (Optional)

```bash
cd ~/MosquitoDetection
python3 scripts/start_dashboard.py
```

Access dashboard at: `http://<raspberry-pi-ip>:5000`

See `docs/DASHBOARD.md` for detailed instructions.

## Troubleshooting

### Camera not detected

1. Check CSI ribbon cable connection
2. Verify camera is enabled:

```bash
vcgencmd get_camera
```

Should show: `supported=1 detected=1`

3. Check camera module:

```bash
lsmod | grep bcm2835
```

4. See `docs/CAMERA_TROUBLESHOOTING.md` for detailed help

### Model file not found

Copy the model file manually:

```bash
scp models/model.tflite khanhtuong@raspberrypi.local:~/MosquitoDetection/models/
```

### Dependencies not installed

If setup failed due to package conflicts, run setup again:

```bash
cd ~/MosquitoDetection
chmod +x deployment/setup.sh
./deployment/setup.sh
```

### Service not starting

Check logs:

```bash
journalctl -u mosquito-demo.service -n 50
```

Check service file:

```bash
sudo systemctl cat mosquito-demo.service
```

### TensorFlow Lite version error

If you see error: `Didn't find op for builtin opcode 'FULLY_CONNECTED' version '12'`

This means the model was converted with TensorFlow 2.13+ but tflite-runtime on Raspberry Pi only supports older ops.

**Solution: Convert model with compatibility mode**

1. **On Windows machine**, convert the model:

```powershell
cd D:\Python\TinyML_MosquitoDetection\MosquitoDetection
python scripts/convert_model_compatible.py --model models/mobilenetv2.h5 --output models/model_compatible.tflite
```

2. **Copy to Raspberry Pi**:

```powershell
scp models/model_compatible.tflite khanhtuong@raspberrypi.local:~/MosquitoDetection/models/model.tflite
```

3. **Test on Raspberry Pi**:

```bash
python3 scripts/demo.py
```

## Files Structure on Raspberry Pi

```
~/MosquitoDetection/
├── config.py              # Configuration
├── main.py                # Main entry point
├── models/
│   └── model.tflite      # Trained model (required)
├── src/                   # Source code
├── data/
│   └── detections.db     # SQLite database (auto-created)
└── logs/                  # Log files
```

## Next Steps

- View detection history: Use web dashboard or `scripts/view_daily_density.py`
- Retrain model: See `docs/TRAINING.md`
- Monitor performance: Check logs in `logs/` directory
