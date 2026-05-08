# LEGO Object Detection Training PRD

## Project Title
Development of a LEGO Object Detection Model for an Educational Pick-and-Place Robotic Arm

---

# Overview

This project focuses on training a machine learning object detection model capable of detecting and classifying LEGO bricks used in our thesis project titled:

**"Development of a Cost-Effective 3D-Printed Pick and Place Robotic Arm for Object Sorting and Educational Applications"**

The trained model will be integrated into a 5-DOF robotic arm system to support automated LEGO sorting using computer vision.

The object detection system must operate reliably in a classroom or laboratory environment and support real-time detection for automated pick-and-place operations.

---

# Thesis Scope Alignment

The object detection model must strictly follow the LEGO scope defined in the thesis paper.

The target objects are:

- Standard rectangular LEGO bricks made from ABS plastic
- Sizes ranging from:
  - 1×1 (8 mm × 8 mm × 9.6 mm)
  - up to 2×8 (16 mm × 64 mm × 9.6 mm)
- Possible larger variations:
  - 2×10
  - 2×12
- Colors include:
  - Red
  - Blue
  - Yellow
  - Green
  - Black
  - White

These LEGO bricks will serve as the primary objects for:

- Object detection
- Automated sorting
- Pick-and-place evaluation
- Accuracy testing
- Robotic arm automation

---

# Project Goal

Train a lightweight and accurate object detection model capable of:

1. Detecting LEGO bricks in real time
2. Supporting automated robotic sorting
3. Running efficiently on low-cost hardware
4. Achieving at least:
   - 0.70 mAP for object detection
   - 90% sorting success rate during robotic operation

---

# Available Datasets

The project folder contains the following downloaded Kaggle LEGO datasets:

## Dataset 1
### `lego-brick-images`

Source:
- Images of LEGO Bricks
- Approximately 40,000 images
- 50 LEGO brick classes

Purpose:
- Auxiliary dataset
- Potential classification support
- Optional for detection training if annotations are available

Folder Name:
```text
lego-brick-images
```

---

## Dataset 2
### `synthetic-lego-brick-dataset-for-object-detection`

Source:
- Synthetic LEGO brick object detection dataset
- Includes tutorials for Blender, YOLOv5, and SSD

Purpose:
- Primary synthetic training dataset
- Main baseline training dataset

Folder Name:
```text
synthetic-lego-brick-dataset-for-object-detection
```

---

## Dataset 3
### `spiled-lego-bricks`

Source:
- Real-world LEGO brick detection dataset
- Designed for object detection tasks

Purpose:
- Primary real-world validation and fine-tuning dataset
- Used to improve generalization and real-world performance

Folder Name:
```text
spiled-lego-bricks
```

---

# Dataset Usage Strategy

## Priority Order

### Primary Dataset
Use:
```text
synthetic-lego-brick-dataset-for-object-detection
```

Purpose:
- Initial training
- Shape learning
- Synthetic environment pretraining

---

### Secondary Dataset
Use:
```text
spiled-lego-bricks
```

Purpose:
- Fine-tuning
- Real-world adaptation
- Validation and testing

---

### Optional Dataset
Use:
```text
lego-brick-images
```

ONLY IF:
- Bounding-box annotations exist
- Annotation conversion is possible

Otherwise:
- Skip for object detection training
- Use only as supplementary visual data

---

# Detection Classes

The detection classes must follow the thesis scope and NOT every LEGO piece available in the datasets.

Preferred detection classes:

```text
1x1
1x2
2x2
2x4
2x6
2x8
2x10
2x12
```

If datasets contain inconsistent labels:

- Create a label mapping system
- Normalize labels across datasets
- Merge equivalent class names
- Ignore unsupported LEGO piece types

---

# Model Selection

## Required Model
Use:

```text
Ultralytics YOLO Object Detection Model
```

Recommended starting models:

```text
yolov8n.pt
yolov8s.pt
```

Preferred initial model:

```text
yolov8n.pt
```

Reason:
- Lightweight
- Fast inference
- Good for educational robotics
- Suitable for low-cost hardware
- Easier real-time deployment

---

# Training Workflow

## Stage 1 — Synthetic Baseline Training

Train using:

```text
synthetic-lego-brick-dataset-for-object-detection
```

Goals:
- Learn LEGO shapes
- Learn object boundaries
- Learn brick geometry
- Establish baseline mAP

---

## Stage 2 — Real-World Fine-Tuning

Fine-tune using:

```text
spiled-lego-bricks
```

Goals:
- Improve real-world robustness
- Handle shadows and lighting
- Handle cluttered scenes
- Improve detection stability

---

## Stage 3 — Final Evaluation

Evaluate using:
- Held-out real-world test set
- Separate validation images

Goals:
- Measure final mAP
- Measure precision and recall
- Measure inference speed
- Validate robotic sorting readiness

---

# Training Parameters

Use the following baseline training configuration.

## Core Training Parameters

```yaml
model: yolov8n.pt
epochs: 100
batch: 16
imgsz: 640
patience: 20
optimizer: AdamW
pretrained: true
seed: 42
deterministic: true
workers: 8
save: true
save_period: 10
cache: true
amp: true
```

---

## Learning Rate Parameters

```yaml
lr0: 0.001
lrf: 0.01
momentum: 0.937
weight_decay: 0.0005
warmup_epochs: 3
warmup_momentum: 0.8
warmup_bias_lr: 0.1
cos_lr: true
```

---

## Layer Freezing Strategy

During early training:

```yaml
freeze: 10
```

Purpose:
- Preserve pretrained backbone features
- Stabilize early training
- Prevent catastrophic forgetting

Later:
- Unfreeze layers during fine-tuning
- Allow domain adaptation to LEGO data

---

# Loss Function Parameters

Use:

```yaml
box: 7.5
cls: 0.5
dfl: 1.5
```

If class imbalance occurs:

```yaml
cls_pw: 0.25
```

Increase only if rare classes perform poorly.

---

# Data Augmentation

## Required Augmentations

```yaml
mosaic: 1.0
mixup: 0.0
cutmix: 0.0
fliplr: 0.5
flipud: 0.0
rect: false
multi_scale: 0.0
close_mosaic: 10
```

Purpose:
- Improve generalization
- Improve robustness to object positioning
- Improve detection consistency

---

# Dataset Preparation Requirements

Claude Code must automatically:

1. Scan all dataset folders
2. Detect annotation formats
3. Convert labels to one common format
4. Remove duplicate images
5. Detect corrupted files
6. Validate bounding boxes
7. Normalize class names
8. Generate dataset YAML file
9. Split datasets properly
10. Generate training statistics

---

# Dataset Split

Use:

```text
70% Training
15% Validation
15% Testing
```

Important:
- Prevent data leakage
- Keep images from the same scene together
- Preserve class balance

---

# Required Experiments

## Experiment 1 — Synthetic Only

Train only on:

```text
synthetic-lego-brick-dataset-for-object-detection
```

Measure:
- Baseline mAP
- Stability
- Generalization

---

## Experiment 2 — Synthetic + Real-World

Train using:

- Synthetic dataset
- Real-world fine-tuning

Measure:
- Improvement in real-world accuracy
- Generalization performance
- Sorting readiness

---

## Experiment 3 — Optional Extended Training

Use:

```text
lego-brick-images
```

ONLY IF:
- Bounding boxes exist
- Annotation conversion is possible

Otherwise:
- Skip this experiment

---

# Evaluation Metrics

Claude Code must report:

```text
mAP@0.5
mAP@0.5:0.95
Precision
Recall
F1 Score
Per-class AP
Confusion Matrix
Inference Time
FPS
```

---

# Success Criteria

The final trained model must:

- Achieve at least 0.70 mAP
- Detect LEGO bricks reliably
- Work under classroom lighting conditions
- Support near real-time robotic sorting
- Perform well on real-world images
- Avoid severe overfitting

---

# Expected Outputs

Claude Code must generate:

## Training Files

```text
train.py
validate.py
test.py
dataset.yaml
label_mapping.json
```

---

## Model Outputs

```text
best.pt
last.pt
```

---

## Reports

```text
training_curves.png
confusion_matrix.png
metrics_report.txt
```

---

# Important Notes

## Weights and Biases

Do NOT manually hardcode final weights and biases.

Requirements:
- Start from pretrained YOLO weights
- Allow optimizer to learn weights automatically
- Use warmup strategy for stable convergence

---

# Deployment Requirements

The final model must support:

- Real-time LEGO detection
- Integration with robotic arm sorting logic
- Bounding-box output for pick-and-place
- ESP32-based robotic workflow integration
- Educational demonstrations

---

# Final Objective

Develop a lightweight, accurate, and robust LEGO object detection model that can be integrated into the thesis robotic arm system for educational automated sorting applications.

