# Google Colab - Quick Reference Card

One-page quick reference for running LEGO detection training on Colab.

---

## 🚀 Setup (5 minutes)

```python
# 1. Enable GPU
Runtime → Change runtime type → GPU → Save

# 2. Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# 3. Navigate to project
%cd /content/drive/MyDrive/block-coding-robot

# 4. Install dependencies
!pip install -q ultralytics opencv-python pillow pandas matplotlib seaborn pyyaml tqdm scikit-learn xmltodict tensorboard

# 5. Verify GPU
import torch
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
```

---

## 📁 Upload Project to Google Drive

**Method 1: Via Google Drive Web**
1. Compress project: `zip -r project.zip block-coding-robot/`
2. Upload to: `My Drive/block-coding-robot/`
3. Extract in Drive

**Method 2: Via Colab**
```python
from google.colab import files
uploaded = files.upload()  # Select zip
!unzip -q project.zip
```

---

## 🎯 Training Commands

```bash
# Prepare datasets (10 min)
!python prepare_datasets.py

# Train Experiment 2 (2-4 hrs with GPU)
!python train.py --experiment 2

# Validate
!python validate.py --model training_output/models/experiment_2_*/stage2_finetuned/weights/best.pt --experiment 2

# Test & Benchmark
!python test.py --model <path-to-best.pt> --image test.jpg --benchmark

# Export to TFLite
!python export_model.py --model <path-to-best.pt> --format tflite
```

---

## 📊 Monitoring

```python
# TensorBoard
%load_ext tensorboard
%tensorboard --logdir training_output/models/

# Check training progress
!tail -20 training_output/models/experiment_2_*/stage2_finetuned/results.csv

# GPU usage
!nvidia-smi

# Disk space
!df -h
```

---

## 💾 Download Results

```python
# Zip results
!zip -r results.zip training_output/

# Download
from google.colab import files
files.download('results.zip')

# Or download specific files
files.download('training_output/models/experiment_2_TIMESTAMP/stage2_finetuned/weights/best.pt')
```

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| No GPU | Runtime → Change runtime → GPU |
| Out of memory | Reduce batch size in `config.py` to 8 |
| Session timeout | Models auto-save to Drive every epoch |
| Can't find files | Check path: `!ls /content/drive/MyDrive/` |
| Disconnected | Resume: `--resume last.pt` |

---

## ⏱️ Timeline

```
Setup:              5 min
Dataset prep:      10 min
Training (Exp 2):  3 hrs (GPU)
Validation:         5 min
Testing:            5 min
Export:             3 min
─────────────────────────
TOTAL:           ~4 hrs
```

---

## 🎓 Expected Results

```
mAP@0.5:       0.75+ (target: 0.70)
Precision:     0.78+ (target: 0.75)
Recall:        0.72+ (target: 0.70)
Inference:    15-20ms (target: <100ms)
```

---

## 📂 Output Location

```
/content/drive/MyDrive/block-coding-robot/training_output/
├── models/experiment_2_TIMESTAMP/stage2_finetuned/weights/best.pt ← YOUR MODEL
├── results/validation_best/metrics.json
└── results/thesis_graphs/*.png
```

---

## 🔗 Quick Links

- **Open Colab**: https://colab.research.google.com/
- **Notebook**: Upload `LEGO_Detection_Training.ipynb`
- **Documentation**: See `COLAB_SETUP_GUIDE.md` for full guide

---

## ✅ Checklist

- [ ] GPU enabled
- [ ] Drive mounted
- [ ] Project uploaded
- [ ] Datasets uploaded
- [ ] Dependencies installed
- [ ] Training started
- [ ] Results downloaded

---

**Training on Colab: 4 hours vs 25+ hours on CPU!** 🚀
