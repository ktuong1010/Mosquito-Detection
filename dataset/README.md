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


