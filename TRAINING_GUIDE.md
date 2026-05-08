# LEGO Object Detection Training Guide

Complete guide for training YOLOv8 models to detect LEGO bricks for the robotic arm thesis project.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Dataset Preparation](#dataset-preparation)
4. [Training Experiments](#training-experiments)
5. [Model Validation](#model-validation)
6. [Testing & Inference](#testing--inference)
7. [Generating Thesis Graphs](#generating-thesis-graphs)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware Requirements

- **RAM**: Minimum 8GB (16GB recommended)
- **GPU**: NVIDIA GPU with CUDA support (optional but **highly recommended**)
  - Training on CPU is 10-50x slower
  - Without GPU, expect 10-20 hours per experiment
- **Storage**: At least 10GB free disk space

### Software Requirements

- **Python**: 3.8 or higher (you have 3.14.4 ✓)
- **Operating System**: Windows 10/11, Linux, or macOS
- **Internet**: Required for downloading PyTorch and dependencies

---

## Environment Setup

### Step 1: Install Dependencies

Run the automated setup script:

```bash
python setup_environment.py
```

This script will:
- Check Python version
- Install all required packages (PyTorch, Ultralytics YOLOv8, OpenCV, etc.)
- Verify GPU availability
- Display system information

**Expected output:**
```
✓ Python version OK
✓ PyTorch 2.x.x
  CUDA available: True/False
✓ Ultralytics 8.x.x
✓ OpenCV 4.x.x
✓ Environment setup complete!
```

**If installation fails:**
```bash
# Manual installation
pip install -r requirements.txt
```

### Step 2: Verify GPU (Optional but Recommended)

Check if CUDA is available:

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

**Without GPU:**
- Training will use CPU (slower)
- Reduce batch size to 8 or 4 if you run out of RAM
- Consider using Google Colab with free GPU

---

## Dataset Preparation

Your datasets are located in the `datasets/` folder:
- **Synthetic dataset**: `datasets/images/` + `datasets/YOLO_ready_txt_labels/`
- **Real-world dataset**: `datasets/images/` + `datasets/annotations/` (XML format)
- **Optional dataset**: `datasets/LEGO brick images v1/` (classification only)

### Step 3: Prepare Datasets

Run the dataset preparation script:

```bash
python prepare_datasets.py
```

**This script will:**
1. ✅ Scan all dataset folders
2. ✅ Convert XML annotations to YOLO format
3. ✅ Map labels to target classes (1x1, 1x2, 2x2, 2x4, 2x6, 2x8, 2x10, 2x12)
4. ✅ Remove duplicate images
5. ✅ Detect and skip corrupted files
6. ✅ Validate bounding boxes
7. ✅ Split data: 70% train, 15% val, 15% test
8. ✅ Generate `data.yaml` configuration files
9. ✅ Create statistics report

**Expected output:**
```
Processing Synthetic Dataset
Found X label files
✓ Processed X valid synthetic images

Processing Real-World Dataset
Found X XML annotation files
✓ Processed X valid real-world images

Dataset split complete
  Train: X images (70%)
  Val: X images (15%)
  Test: X images (15%)

Dataset Statistics
  Class Distribution:
    1x1: X
    1x2: X
    2x2: X
    ...
```

**Output files:**
```
training_output/
└── prepared_datasets/
    ├── experiment_1/
    │   ├── train/images/ + train/labels/
    │   ├── val/images/ + val/labels/
    │   ├── test/images/ + test/labels/
    │   ├── data.yaml
    │   └── dataset_statistics.json
    └── experiment_2/
        └── (same structure)
```

---

## Training Experiments

According to the PRD, we have 3 experiments:

### Experiment 1: Synthetic Only (Baseline)

Train only on synthetic dataset to establish baseline performance.

```bash
python train.py --experiment 1
```

**What happens:**
- Loads YOLOv8n pretrained weights
- Trains for 100 epochs on synthetic data
- Batch size: 16, Image size: 640
- Uses data augmentation (mosaic, fliplr)
- Saves best model based on validation mAP
- Generates training curves and metrics

**Training time:**
- With GPU: 1-3 hours
- Without GPU: 10-20 hours

**Expected mAP:** 0.50 - 0.70 (synthetic data only)

---

### Experiment 2: Synthetic + Real-World (Recommended)

Two-stage training: synthetic baseline → fine-tune on real-world data.

```bash
python train.py --experiment 2
```

**What happens:**
- **Stage 1:** Train on synthetic data (same as Experiment 1)
- **Stage 2:** Fine-tune on real-world + synthetic data
  - Starts from Stage 1 best weights
  - Unfreezes all layers
  - Lower learning rate (0.0001 vs 0.001)
  - Trains for 50 additional epochs

**Training time:**
- With GPU: 2-5 hours (both stages)
- Without GPU: 15-30 hours

**Expected mAP:** 0.65 - 0.80 (better generalization)

---

### Experiment 3: Extended Training (Optional)

Include `lego-brick-images` dataset if annotations exist.

```bash
python train.py --experiment 3
```

**Status:** Not implemented yet
- Requires annotation conversion for classification dataset
- Use Experiment 2 for best results

---

## Monitoring Training Progress

### TensorBoard (Recommended)

View training metrics in real-time:

```bash
# In a separate terminal
tensorboard --logdir training_output/models/
```

Then open: http://localhost:6006

**Metrics to watch:**
- **mAP@0.5**: Should increase over epochs (target: ≥ 0.70)
- **train/box_loss**: Should decrease steadily
- **val/box_loss**: Should decrease (watch for overfitting)
- **Precision & Recall**: Should balance (both ≥ 0.70)

### Training Logs

Live output shows:
```
Epoch 1/100: 100%|██████████| 50/50 [00:30<00:00, 1.67it/s]
      Class     Images  Instances      P      R  mAP50  mAP50-95
        all        150       450   0.65   0.68   0.67      0.42
```

---

## Model Validation

After training completes, validate the model on the test set:

```bash
python validate.py --model training_output/models/experiment_2_TIMESTAMP/stage2_finetuned/weights/best.pt --experiment 2
```

**Outputs:**
1. **Console report**: Metrics summary
2. **metrics.json**: Detailed metrics
3. **validation_report.txt**: Full text report
4. **per_class_performance.png**: Bar chart of AP per class
5. **metrics_summary.png**: Radar chart + target comparison

**Success criteria (from PRD):**
- ✅ mAP@0.5 ≥ 0.70
- ✅ Precision ≥ 0.75
- ✅ Recall ≥ 0.70

---

## Testing & Inference

### Test on Single Image

```bash
python test.py --model path/to/best.pt --image path/to/test_image.jpg --conf 0.25
```

**Output:**
- Detections printed to console
- Annotated image saved to `training_output/results/predictions_*/`

**Example output:**
```
Processing: test_lego.jpg
  Detections: 5
    [1] 2x4: 0.89
    [2] 2x4: 0.87
    [3] 1x2: 0.92
    [4] 2x2: 0.85
    [5] 1x1: 0.78
  Saved to: training_output/results/predictions_best/pred_test_lego.jpg
```

---

### Batch Inference

Process multiple images:

```bash
python test.py --model path/to/best.pt --batch path/to/image_folder/ --conf 0.25
```

**Output:**
- Statistics printed (detections by class)
- All annotated images saved to batch folder

---

### Benchmark Inference Speed

```bash
python test.py --model path/to/best.pt --image test.jpg --benchmark
```

**Output:**
```
Benchmark Results
  Average inference time: 15.32 ms
  FPS: 65.27
  ✓ Model is suitable for real-time robotics (>= 10 FPS)
```

**Target:** ≤ 100ms per image (for robotic arm sorting)

---

### Visualize Predictions

```bash
python test.py --model path/to/best.pt --image test.jpg --visualize
```

Creates high-quality matplotlib visualization.

---

## Training Configuration

All parameters are defined in `config.py` following the PRD specifications.

### Key Parameters

```python
# Training
epochs = 100
batch_size = 16
image_size = 640
optimizer = "AdamW"
learning_rate = 0.001

# Data Augmentation
mosaic = 1.0          # 100% mosaic augmentation
fliplr = 0.5          # 50% horizontal flip
mixup = 0.0           # Disabled
```

### Adjusting for Low RAM

If you run out of memory, edit `config.py`:

```python
TRAIN_CONFIG = {
    "batch": 8,        # Reduce from 16
    "workers": 4,      # Reduce from 8
    "cache": False,    # Disable caching
}
```

---

## Output Files

After training, you'll have:

```
training_output/
├── prepared_datasets/
│   └── experiment_X/
│       ├── train/ val/ test/
│       ├── data.yaml
│       └── dataset_statistics.json
├── models/
│   └── experiment_X_TIMESTAMP/
│       ├── stage1_synthetic/
│       │   ├── weights/
│       │   │   ├── best.pt       ← Best model (use this)
│       │   │   └── last.pt
│       │   ├── results.csv
│       │   ├── confusion_matrix.png
│       │   └── results.png
│       └── stage2_finetuned/ (for Experiment 2)
└── results/
    └── validation_best/
        ├── metrics.json
        ├── validation_report.txt
        ├── per_class_performance.png
        └── metrics_summary.png
```

**Most important file:** `best.pt` - This is your trained model

---

## Generating Thesis Graphs

After training both experiments, generate **publication-quality comparison graphs** for your thesis results section.

### What Graphs You'll Get

1. **Training Loss Comparison** - 4-panel loss curves across experiments
2. **mAP Progression** - Model performance improvement over epochs
3. **Precision/Recall Curves** - P/R balance during training
4. **Final Metrics Comparison** - Bar chart comparing all experiments
5. **Per-Class Performance** - AP comparison for each LEGO class
6. **Inference Speed** - Real-time capability demonstration
7. **Success Criteria Dashboard** - Visual pass/fail summary
8. **Results Table** - Markdown/LaTeX table for thesis

### Generate All Comparison Graphs

```bash
python generate_thesis_graphs.py \
  --exp1-results training_output/models/experiment_1_TIMESTAMP/stage1_synthetic/results.csv \
  --exp1-metrics training_output/results/validation_exp1/metrics.json \
  --exp2-results training_output/models/experiment_2_TIMESTAMP/stage2_finetuned/results.csv \
  --exp2-metrics training_output/results/validation_exp2/metrics.json
```

**Output:** All graphs saved to `training_output/results/thesis_graphs/`

### Additional Automatic Visualizations

YOLOv8 automatically generates during training:
- Training curves (`results.png`)
- Confusion matrices
- PR curves, F1 curves
- Dataset distribution analysis

See `VISUALIZATION_GUIDE.md` for complete details on all 20+ graphs.

---

## Troubleshooting

### Issue: Out of Memory (OOM)

**Symptoms:** Training crashes with "CUDA out of memory" or system freezes

**Solutions:**
1. Reduce batch size in `config.py`:
   ```python
   "batch": 8  # or even 4
   ```
2. Reduce image size:
   ```python
   "imgsz": 416  # instead of 640
   ```
3. Disable caching:
   ```python
   "cache": False
   ```

---

### Issue: Training is Very Slow

**CPU training:**
- Expected: 10-30 hours for full training
- Solution: Use Google Colab with free GPU
- Or: Reduce epochs to 50 for faster prototyping

**With GPU but still slow:**
- Check GPU utilization: `nvidia-smi`
- Enable AMP (already enabled by default):
  ```python
  "amp": True
  ```

---

### Issue: mAP is Too Low (< 0.70)

**Possible causes:**
1. **Not enough training:** Increase epochs to 150
2. **Class imbalance:** Check `dataset_statistics.json`
3. **Bad annotations:** Some bounding boxes may be incorrect
4. **Need more data:** Combine synthetic + real-world (Experiment 2)

**Solutions:**
- Run Experiment 2 instead of Experiment 1
- Increase training time
- Check dataset statistics for imbalanced classes
- Visualize predictions to see failure modes

---

### Issue: Model Overfits (train mAP >> val mAP)

**Symptoms:** Training mAP = 0.95, Validation mAP = 0.60

**Solutions:**
- Increase data augmentation
- Add more real-world data
- Reduce model capacity (use yolov8n instead of yolov8s)
- Enable dropout (YOLOv8 handles this automatically)

---

### Issue: Inference is Too Slow (< 10 FPS)

**Target:** ≥ 10 FPS for real-time robotic sorting

**Solutions:**
- Use a lighter model: `yolov8n` instead of `yolov8s`
- Reduce image size during inference:
  ```python
  results = model(image, imgsz=320)  # instead of 640
  ```
- Optimize with TensorRT (advanced)
- Run on ESP32: Convert to TFLite format (Week 1+ task)

---

### Issue: Some Classes Never Detected

**Check:**
1. Class distribution in `dataset_statistics.json`
2. Per-class AP in validation report

**If a class has < 50 examples:**
- It won't learn well
- Solution: Augment that class more or collect more data

---

## Next Steps

After training a good model (mAP ≥ 0.70):

1. **Convert to TFLite** for ESP32-CAM deployment
2. **Test on real robotic arm** with classroom lighting
3. **Fine-tune** if performance degrades in production
4. **Document** results in thesis

---

## Success Criteria Summary

According to PRD, your model must achieve:

| Metric | Target | Purpose |
|--------|--------|---------|
| mAP@0.5 | ≥ 0.70 | Overall detection accuracy |
| Precision | ≥ 0.75 | Minimize false positives |
| Recall | ≥ 0.70 | Minimize missed detections |
| Inference Time | ≤ 100ms | Real-time sorting |
| Sorting Success | 90% | End-to-end robotic performance |

---

## Quick Reference Commands

```bash
# 1. Setup environment
python setup_environment.py

# 2. Prepare datasets
python prepare_datasets.py

# 3. Train model (recommended: Experiment 2)
python train.py --experiment 2

# 4. Validate model
python validate.py --model path/to/best.pt --experiment 2

# 5. Test on image
python test.py --model path/to/best.pt --image test.jpg --visualize --benchmark

# 6. Monitor training (optional)
tensorboard --logdir training_output/models/
```

---

## Contact & Support

For questions about this training pipeline:
- Check this guide first
- Review PRD specifications in `prd.md`
- Inspect configuration in `config.py`
- Check TensorBoard for training insights

**Good luck with your thesis project! 🎓🤖**
