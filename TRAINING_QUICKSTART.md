# LEGO Object Detection - Training Quick Start

Get started training your LEGO detection model in **3 simple commands**.

---

## ⚡ Quick Start (TL;DR)

```bash
# 1. Install dependencies (5-10 min)
python setup_environment.py

# 2. Prepare datasets (5-15 min)
python prepare_datasets.py

# 3. Train best model (2-5 hrs GPU / 15-30 hrs CPU)
python train.py --experiment 2
```

**That's it!** Your trained model will be at:
```
training_output/models/experiment_2_TIMESTAMP/stage2_finetuned/weights/best.pt
```

---

## 📊 After Training (Optional but Recommended)

### Validate Performance
```bash
python validate.py --model <path-to-best.pt> --experiment 2
```

### Test on Images
```bash
python test.py --model <path-to-best.pt> --image test.jpg --visualize --benchmark
```

### Generate Thesis Graphs
```bash
python generate_thesis_graphs.py \
  --exp1-results <exp1-results.csv> \
  --exp1-metrics <exp1-metrics.json> \
  --exp2-results <exp2-results.csv> \
  --exp2-metrics <exp2-metrics.json>
```

---

## 🎯 Success Criteria

Your model should achieve:

| Metric | Target | How to Check |
|--------|--------|--------------|
| mAP@0.5 | ≥ 0.70 | `validate.py` output |
| Precision | ≥ 0.75 | `validate.py` output |
| Recall | ≥ 0.70 | `validate.py` output |
| Inference Time | ≤ 100ms | `test.py --benchmark` |

---

## 📖 Full Documentation

- **TRAINING_GUIDE.md** - Complete step-by-step guide
- **VISUALIZATION_GUIDE.md** - All 20+ graphs explained
- **TRAINING_CHECKLIST.md** - Track your progress
- **TRAINING_PIPELINE_SUMMARY.md** - Feature overview

---

**Good luck with your thesis! 🎓🤖**
