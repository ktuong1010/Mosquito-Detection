# Dataset Directory

This directory contains the training dataset for the mosquito detection model.

## Structure

The dataset should be organized as follows:

```
dataset/
├── processed_edgeimpulse/    # Processed dataset for training
│   ├── train/
│   │   ├── Aedes/
│   │   │   └── [image files]
│   │   └── Culex/
│   │       └── [image files]
│   └── val/
│       ├── Aedes/
│       │   └── [image files]
│       └── Culex/
│           └── [image files]
└── raw/                      # Raw dataset (optional)
    └── [original images]
```

## Transferring Dataset to Raspberry Pi

### Method 1: Using SCP

From your computer:

```bash
scp -r dataset/processed_edgeimpulse pi@raspberrypi.local:~/MosquitoDetection/dataset/
```

### Method 2: Using rsync (Recommended)

Better for large datasets with progress tracking:

```bash
rsync -avz --progress dataset/processed_edgeimpulse/ \
    pi@raspberrypi.local:~/MosquitoDetection/dataset/processed_edgeimpulse/
```

### Method 3: Using USB Drive

1. Copy dataset to USB drive on your computer
2. Connect USB drive to Raspberry Pi
3. Copy from USB:

```bash
# Mount USB drive (usually /media/pi/USB_NAME)
cp -r /media/pi/USB_NAME/processed_edgeimpulse ~/MosquitoDetection/dataset/
```

## Dataset Requirements

- **Format**: JPEG images
- **Size**: 224x224 pixels (will be resized during training)
- **Classes**: 
  - Aedes (Aedes Aegypti, Aedes Albopictus)
  - Culex
- **Minimum samples**: 
  - Training: At least 100 images per class
  - Validation: At least 20 images per class

## Preparing Dataset

If you need to prepare the dataset from raw images, use the preparation script:

```bash
python3 scripts/prepare_edge_impulse_dataset.py --input-dir dataset/raw --output-dir dataset/processed_edgeimpulse
```

## Notes

- Dataset files are not committed to git due to size
- Keep dataset organized for easy transfer
- Ensure sufficient disk space on Raspberry Pi (at least 2GB free)
- Consider compressing dataset for transfer if needed

