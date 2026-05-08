# LEGO Object Detection Training Pipeline - Visual Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LEGO OBJECT DETECTION TRAINING PIPELINE                  │
│                         YOLOv8 for Robotic Arm Thesis                       │
└─────────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║                          PHASE 1: SETUP                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────┐
    │ Run Setup       │     python setup_environment.py
    │ Environment     │
    └────────┬────────┘
             │
             v
    ┌─────────────────────────────────────────────┐
    │  Install Dependencies                       │
    │  ✓ PyTorch 2.0+                            │
    │  ✓ Ultralytics YOLOv8                      │
    │  ✓ OpenCV                                   │
    │  ✓ TensorBoard                             │
    └────────┬────────────────────────────────────┘
             │
             v
    ┌─────────────────┐
    │ Check GPU       │
    │ CUDA Available? │
    └────┬────────────┘
         │
    ┌────┴────┐
    │ YES     │ NO
    v         v
  Fast     Slow
  (GPU)    (CPU)


╔═══════════════════════════════════════════════════════════════════════════╗
║                    PHASE 2: DATASET PREPARATION                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

    ┌─────────────────────────────────────────────────────────────┐
    │                     Input Datasets                          │
    ├─────────────────────────────────────────────────────────────┤
    │ 1. Synthetic Dataset (YOLO format)                          │
    │    - images/ + YOLO_ready_txt_labels/                       │
    │                                                              │
    │ 2. Real-World Dataset (XML format)                          │
    │    - images/ + annotations/ (Pascal VOC)                    │
    │                                                              │
    │ 3. Optional Dataset (Classification only)                   │
    │    - LEGO brick images v1/                                  │
    └───────────────────────┬─────────────────────────────────────┘
                            │
                            v
            ┌───────────────────────────────┐
            │  prepare_datasets.py          │
            └───────────────┬───────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         v                  v                  v
    ┌────────┐        ┌────────┐        ┌────────┐
    │ Scan   │        │Convert │        │Validate│
    │ Files  │   →    │Labels  │   →    │Bounding│
    │        │        │to YOLO │        │  Boxes │
    └────────┘        └────────┘        └────────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            v
                    ┌───────────────┐
                    │ Map to 8      │
                    │ Target Classes│
                    │ (1x1→2x12)    │
                    └───────┬───────┘
                            │
         ┌──────────────────┼──────────────────┐
         v                  v                  v
    ┌────────┐        ┌────────┐        ┌────────┐
    │Remove  │        │Detect  │        │Split   │
    │Duplicat│   →    │Corrupt │   →    │70/15/15│
    │  es    │        │ Images │        │        │
    └────────┘        └────────┘        └────────┘
                            │
                            v
    ┌─────────────────────────────────────────────┐
    │           Output: Prepared Dataset          │
    ├─────────────────────────────────────────────┤
    │ • train/ (70%)                              │
    │ • val/   (15%)                              │
    │ • test/  (15%)                              │
    │ • data.yaml                                 │
    │ • dataset_statistics.json                   │
    └─────────────────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                   PHASE 3: MODEL TRAINING                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────┐
│                       EXPERIMENT 1: Synthetic Only                        │
└───────────────────────────────────────────────────────────────────────────┘

    python train.py --experiment 1

    ┌─────────────────┐
    │  YOLOv8n.pt     │
    │  (pretrained)   │
    └────────┬────────┘
             │
             v
    ┌─────────────────────────────────┐
    │  Train on Synthetic Dataset     │
    │  • 100 epochs                   │
    │  • Batch: 16, ImgSize: 640      │
    │  • AdamW optimizer              │
    │  • Data augmentation enabled    │
    └────────┬────────────────────────┘
             │
             v
    ┌─────────────────┐
    │  Stage 1 Best   │     Expected mAP: 0.50-0.70
    │  Model          │
    └─────────────────┘


┌───────────────────────────────────────────────────────────────────────────┐
│              EXPERIMENT 2: Synthetic + Real-World (Best)                  │
└───────────────────────────────────────────────────────────────────────────┘

    python train.py --experiment 2

    ┌─────────────────┐
    │  YOLOv8n.pt     │
    │  (pretrained)   │
    └────────┬────────┘
             │
             v
    ┌──────────────────────────────────┐
    │   STAGE 1: Synthetic Training    │
    │   • 100 epochs                   │
    │   • Learn LEGO shapes/geometry   │
    │   • Freeze 10 layers initially   │
    └────────┬─────────────────────────┘
             │
             v
    ┌─────────────────┐
    │  Stage 1 Best   │
    │  Weights        │
    └────────┬────────┘
             │
             v
    ┌──────────────────────────────────┐
    │   STAGE 2: Real-World Fine-Tune  │
    │   • 50 epochs                    │
    │   • Lower LR (0.0001)            │
    │   • Unfreeze all layers          │
    │   • Adapt to real lighting       │
    └────────┬─────────────────────────┘
             │
             v
    ┌─────────────────┐
    │  Stage 2 Best   │     Expected mAP: 0.65-0.80 ⭐
    │  Model (FINAL)  │
    └─────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                     PHASE 4: VALIDATION                                   ║
╚═══════════════════════════════════════════════════════════════════════════╝

    python validate.py --model best.pt --experiment 2

    ┌─────────────────┐
    │  Trained Model  │
    │    (best.pt)    │
    └────────┬────────┘
             │
             v
    ┌─────────────────────────────────┐
    │   Run on Test Set               │
    │   • Calculate mAP@0.5           │
    │   • Calculate Precision/Recall  │
    │   • Per-class AP                │
    │   • Confusion matrix            │
    └────────┬────────────────────────┘
             │
             v
    ┌──────────────────────────────────────────┐
    │         Success Criteria Check           │
    ├──────────────────────────────────────────┤
    │  ✓ mAP@0.5 ≥ 0.70        [ ] PASS       │
    │  ✓ Precision ≥ 0.75      [ ] PASS       │
    │  ✓ Recall ≥ 0.70         [ ] PASS       │
    └────────┬─────────────────────────────────┘
             │
     ┌───────┴────────┐
     v                v
   PASS            FAIL
     │                │
     v                v
  Deploy       Retrain/Tune


╔═══════════════════════════════════════════════════════════════════════════╗
║                   PHASE 5: TESTING & INFERENCE                            ║
╚═══════════════════════════════════════════════════════════════════════════╝

    python test.py --model best.pt --image test.jpg

    ┌─────────────────┐
    │   Test Image    │
    └────────┬────────┘
             │
             v
    ┌─────────────────────────────────┐
    │   Model Inference               │
    │   • Detect LEGO bricks          │
    │   • Get bounding boxes          │
    │   • Get class predictions       │
    │   • Get confidence scores       │
    └────────┬────────────────────────┘
             │
             v
    ┌─────────────────────────────────┐
    │   Benchmark Speed               │
    │   • Measure inference time      │
    │   • Calculate FPS               │
    │   • Target: ≤100ms, ≥10 FPS     │
    └────────┬────────────────────────┘
             │
             v
    ┌─────────────────────────────────┐
    │   Output                        │
    │   • Annotated images            │
    │   • Detection statistics        │
    │   • Performance metrics         │
    └─────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                    PHASE 6: MODEL EXPORT                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

    python export_model.py --model best.pt --format tflite

    ┌─────────────────┐
    │  YOLOv8 Model   │
    │   (best.pt)     │
    └────────┬────────┘
             │
         ┌───┴────┬────────┬──────────┐
         v        v        v          v
    ┌──────┐ ┌──────┐ ┌──────┐  ┌────────┐
    │ ONNX │ │TFLite│ │Torch │  │OpenVINO│
    │      │ │  ⭐  │ │Script│  │        │
    └──────┘ └───┬──┘ └──────┘  └────────┘
                 │
                 v
        ┌─────────────────┐
        │  For ESP32-CAM  │
        │  • Quantize INT8│
        │  • TFLite Micro │
        │  • Embed in FW  │
        └─────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                        FILE ORGANIZATION                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

block-coding-robot/
│
├── Training Scripts (7 files)
│   ├── setup_environment.py      ← Step 1: Install dependencies
│   ├── config.py                 ← Configuration hub
│   ├── prepare_datasets.py       ← Step 2: Process datasets
│   ├── train.py                  ← Step 3: Train models
│   ├── validate.py               ← Step 4: Validate performance
│   ├── test.py                   ← Step 5: Run inference
│   └── export_model.py           ← Step 6: Export formats
│
├── Documentation (4 files)
│   ├── prd.md                    ← Original requirements
│   ├── TRAINING_GUIDE.md         ← Complete usage guide
│   ├── TRAINING_PIPELINE_SUMMARY.md
│   ├── TRAINING_CHECKLIST.md     ← Progress tracker
│   └── PIPELINE_OVERVIEW.md      ← This file
│
├── Configuration
│   └── requirements.txt          ← Python dependencies
│
├── Datasets
│   └── datasets/
│       ├── images/               ← Synthetic + real images
│       ├── YOLO_ready_txt_labels/
│       ├── annotations/          ← XML annotations
│       └── LEGO brick images v1/
│
└── Output Structure
    └── training_output/
        ├── prepared_datasets/
        │   ├── experiment_1/
        │   │   ├── train/ val/ test/
        │   │   ├── data.yaml
        │   │   └── dataset_statistics.json
        │   └── experiment_2/
        │       └── (same structure)
        │
        ├── models/
        │   ├── experiment_1_TIMESTAMP/
        │   │   └── stage1_synthetic/
        │   │       ├── weights/
        │   │       │   ├── best.pt ⭐
        │   │       │   └── last.pt
        │   │       └── visualizations/
        │   └── experiment_2_TIMESTAMP/
        │       ├── stage1_synthetic/
        │       └── stage2_finetuned/
        │           ├── weights/
        │           │   └── best.pt ⭐⭐ (USE THIS)
        │           └── visualizations/
        │
        ├── results/
        │   ├── validation_best/
        │   │   ├── metrics.json
        │   │   ├── validation_report.txt
        │   │   └── visualizations/
        │   └── predictions_best/
        │       └── annotated_images/
        │
        └── logs/
            └── tensorboard/


╔═══════════════════════════════════════════════════════════════════════════╗
║                        KEY CONFIGURATIONS                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

Target Classes (8 classes):
┌──────────────────────────────────────┐
│  0: 1x1   │  1: 1x2   │  2: 2x2     │
│  3: 2x4   │  4: 2x6   │  5: 2x8     │
│  6: 2x10  │  7: 2x12                │
└──────────────────────────────────────┘

Training Hyperparameters:
┌──────────────────────────────────────┐
│  Model: YOLOv8n (3.2M params)       │
│  Epochs: 100 (baseline), 50 (tune)  │
│  Batch: 16                           │
│  Image Size: 640×640                 │
│  Optimizer: AdamW                    │
│  LR: 0.001 → 0.0001                 │
│  Augmentation: Mosaic, Flip, HSV    │
└──────────────────────────────────────┘

Success Criteria:
┌──────────────────────────────────────┐
│  mAP@0.5       ≥ 0.70   (70%)       │
│  Precision     ≥ 0.75   (75%)       │
│  Recall        ≥ 0.70   (70%)       │
│  Inference     ≤ 100ms              │
│  Sorting Rate  ≥ 90%    (E2E)       │
└──────────────────────────────────────┘


╔═══════════════════════════════════════════════════════════════════════════╗
║                         QUICK START                                       ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────────────────────┐
│                    3 COMMANDS TO START TRAINING                           │
└───────────────────────────────────────────────────────────────────────────┘

    1. python setup_environment.py
       └─> Installs dependencies (5-10 min)

    2. python prepare_datasets.py
       └─> Processes datasets (5-15 min)

    3. python train.py --experiment 2
       └─> Trains model (2-5 hrs GPU, 15-30 hrs CPU)

┌───────────────────────────────────────────────────────────────────────────┐
│                  OPTIONAL: MONITOR TRAINING                               │
└───────────────────────────────────────────────────────────────────────────┘

    tensorboard --logdir training_output/models/
    └─> Open http://localhost:6006

┌───────────────────────────────────────────────────────────────────────────┐
│                    AFTER TRAINING COMPLETES                               │
└───────────────────────────────────────────────────────────────────────────┘

    4. python validate.py --model path/to/best.pt --experiment 2
       └─> Validates performance (2-5 min)

    5. python test.py --model path/to/best.pt --image test.jpg --benchmark
       └─> Tests inference (<1 min)

    6. python export_model.py --model path/to/best.pt --format tflite
       └─> Exports for ESP32 (1-3 min)


╔═══════════════════════════════════════════════════════════════════════════╗
║                         EXPECTED TIMELINE                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

WITH GPU:
    Setup:          10 minutes
    Dataset Prep:   10 minutes
    Training:       3 hours (Experiment 2, both stages)
    Validation:     5 minutes
    Testing:        5 minutes
    Export:         3 minutes
    ───────────────────────
    TOTAL:          ~4 hours

WITHOUT GPU (CPU):
    Setup:          10 minutes
    Dataset Prep:   10 minutes
    Training:       20 hours (Experiment 2, both stages)
    Validation:     10 minutes
    Testing:        10 minutes
    Export:         5 minutes
    ───────────────────────
    TOTAL:          ~21 hours


╔═══════════════════════════════════════════════════════════════════════════╗
║                    DEPLOYMENT WORKFLOW                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

    Trained Model (best.pt)
           │
           v
    Export to TFLite
           │
           v
    Quantize to INT8
           │
           v
    Convert to TFLite Micro
           │
           v
    Embed in ESP32-CAM Firmware
           │
           v
    Test on Physical Hardware
           │
           v
    Integrate with Robotic Arm
           │
           v
    End-to-End Testing
           │
           v
    Thesis Demonstration


╔═══════════════════════════════════════════════════════════════════════════╗
║                           SUPPORT                                         ║
╚═══════════════════════════════════════════════════════════════════════════╝

Documentation:
    • TRAINING_GUIDE.md        - Complete step-by-step guide
    • TRAINING_CHECKLIST.md    - Progress tracking
    • prd.md                   - Original requirements
    • config.py                - All configurations

Troubleshooting:
    • Out of memory     → Reduce batch size to 8 or 4
    • Training too slow → Use GPU or reduce epochs
    • Low mAP          → Run Experiment 2, increase data
    • Import errors    → Re-run setup_environment.py


═══════════════════════════════════════════════════════════════════════════

                    Ready to train your LEGO detector!
                         Good luck with your thesis! 🎓🤖

═══════════════════════════════════════════════════════════════════════════
