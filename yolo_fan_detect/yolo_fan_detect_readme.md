# YOLO Fan Detection

## Overview

This folder contains a YOLOv8m-based object detection model trained for **fan detection**.

## Model Configuration

| Parameter | Value |
|-----------|-------|
| Model | YOLOv8m (medium) |
| Task | Detection |
| Image Size | 640x640 |
| Batch Size | 128 |
| Epochs | 50 |
| Device | GPU 0,1 |
| Optimizer | Auto |

## Data Augmentation

- Mosaic: 1.0
- MixUp: 0.0
- CopyPaste: 0.0
- Auto Augment: randaugment
- Random Erasing: 0.4

## Output Files

```
yolo_fan_detect/
├── args.yaml              # Full training configuration
├── weights/
│   ├── best.pt            # Best model checkpoint
│   └── last.pt            # Last model checkpoint
├── results.csv            # Training metrics log
├── results.png            # Training loss curves
├── F1_curve.png           # F1 score curve
├── P_curve.png            # Precision curve
├── PR_curve.png           # Precision-Recall curve
├── R_curve.png            # Recall curve
├── confusion_matrix.png   # Confusion matrix
├── confusion_matrix_normalized.png
├── labels.jpg            # Label distribution
├── train_batch*.jpg       # Training batch samples
└── val_batch0_*.jpg       # Validation predictions vs labels
```

## Usage

### Inference with best weights

```python
from ultralytics import YOLO

model = YOLO("weights/best.pt")
results = model.predict(source="your_image.jpg", conf=0.5)
```

### Validate

```bash
yolo detect val model=weights/best.pt data=data.yaml
```

## Training Summary

- **Best mAP50**: See `results.csv` for detailed metrics
- **Best mAP50-95**: See `results.csv` for detailed metrics
- Save directory: `runs/detect/fan2_final`
