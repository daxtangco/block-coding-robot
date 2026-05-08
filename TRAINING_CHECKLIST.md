# LEGO Object Detection Training Checklist

Use this checklist to track your progress through the training pipeline.

---

## Phase 1: Environment Setup

- [ ] **Install dependencies**
  ```bash
  python setup_environment.py
  ```
  - [ ] Python 3.8+ verified
  - [ ] PyTorch installed
  - [ ] Ultralytics YOLOv8 installed
  - [ ] OpenCV installed
  - [ ] GPU availability checked

**Expected time:** 5-10 minutes  
**Success indicator:** ✓ Environment setup complete!

---

## Phase 2: Dataset Preparation

- [ ] **Verify datasets exist**
  - [ ] `datasets/images/` folder exists
  - [ ] `datasets/YOLO_ready_txt_labels/` folder exists
  - [ ] `datasets/annotations/` folder exists (XML files)

- [ ] **Run dataset preparation**
  ```bash
  python prepare_datasets.py
  ```
  - [ ] Synthetic dataset processed
  - [ ] Real-world dataset processed
  - [ ] Dataset statistics generated
  - [ ] Train/val/test splits created

- [ ] **Verify output**
  - [ ] `training_output/prepared_datasets/experiment_1/` exists
  - [ ] `training_output/prepared_datasets/experiment_2/` exists
  - [ ] `data.yaml` files created
  - [ ] `dataset_statistics.json` created

- [ ] **Review statistics**
  - [ ] Check class distribution (all 8 classes present?)
  - [ ] Note any severely imbalanced classes
  - [ ] Note corrupted/duplicate image counts

**Expected time:** 5-15 minutes  
**Success indicator:** ✓ Dataset preparation complete!

---

## Phase 3: Training - Experiment 1 (Optional Baseline)

- [ ] **Start training**
  ```bash
  python train.py --experiment 1
  ```

- [ ] **Monitor training** (optional)
  ```bash
  tensorboard --logdir training_output/models/
  ```
  Open: http://localhost:6006

- [ ] **Wait for completion**
  - [ ] Training finished (100 epochs)
  - [ ] Best model saved
  - [ ] Training curves generated

- [ ] **Record results**
  - Final mAP@0.5: ___________
  - Final Precision: ___________
  - Final Recall: ___________
  - Training time: ___________

**Expected time:** 
- With GPU: 1-3 hours
- With CPU: 10-20 hours

**Success indicator:** Model saved to `stage1_synthetic/weights/best.pt`

---

## Phase 4: Training - Experiment 2 (Recommended)

- [ ] **Start training**
  ```bash
  python train.py --experiment 2
  ```

- [ ] **Monitor progress**
  - [ ] Stage 1 complete (synthetic baseline)
  - [ ] Stage 2 started (fine-tuning)
  - [ ] Stage 2 complete

- [ ] **Record results**
  - **Stage 1:**
    - mAP@0.5: ___________
    - Precision: ___________
    - Recall: ___________
  - **Stage 2 (Fine-tuned):**
    - mAP@0.5: ___________
    - Precision: ___________
    - Recall: ___________
    - Training time: ___________

**Expected time:** 
- With GPU: 2-5 hours (both stages)
- With CPU: 15-30 hours

**Success indicator:** Model saved to `stage2_finetuned/weights/best.pt`

---

## Phase 5: Model Validation

- [ ] **Run validation script**
  ```bash
  python validate.py --model <path-to-best.pt> --experiment 2
  ```

- [ ] **Check success criteria**
  - [ ] mAP@0.5 ≥ 0.70 (target)
  - [ ] Precision ≥ 0.75 (target)
  - [ ] Recall ≥ 0.70 (target)

- [ ] **Review outputs**
  - [ ] `metrics.json` created
  - [ ] `validation_report.txt` created
  - [ ] `per_class_performance.png` created
  - [ ] `metrics_summary.png` created

- [ ] **Analyze per-class performance**
  - Classes performing well (AP > 0.7): ___________________
  - Classes performing poorly (AP < 0.5): ___________________
  - Action needed: ___________________

**Expected time:** 2-5 minutes  
**Success indicator:** ✓ Model meets all success criteria!

---

## Phase 6: Inference Testing

- [ ] **Test on single image**
  ```bash
  python test.py --model <path-to-best.pt> --image <test-image.jpg> --visualize
  ```
  - [ ] Detections printed
  - [ ] Annotated image created
  - [ ] Visual quality acceptable

- [ ] **Benchmark inference speed**
  ```bash
  python test.py --model <path-to-best.pt> --image <test-image.jpg> --benchmark
  ```
  - Average inference time: ___________ ms
  - FPS: ___________
  - [ ] Inference time ≤ 100ms (target for real-time)

- [ ] **Test on batch**
  ```bash
  python test.py --model <path-to-best.pt> --batch <image-folder> --conf 0.25
  ```
  - [ ] Batch statistics generated
  - [ ] All images processed successfully

**Expected time:** < 5 minutes  
**Success indicator:** FPS ≥ 10 for real-time robotics

---

## Phase 7: Model Export (For Deployment)

- [ ] **Export to ONNX**
  ```bash
  python export_model.py --model <path-to-best.pt> --format onnx
  ```
  - [ ] ONNX model created

- [ ] **Export to TFLite** (for ESP32-CAM)
  ```bash
  python export_model.py --model <path-to-best.pt> --format tflite
  ```
  - [ ] TFLite model created
  - [ ] Model size noted: ___________ MB

- [ ] **Export all formats** (optional)
  ```bash
  python export_model.py --model <path-to-best.pt> --format all
  ```

**Expected time:** 1-3 minutes  
**Success indicator:** TFLite model ready for ESP32 deployment

---

## Phase 8: Documentation & Results

- [ ] **Organize results**
  - [ ] Best model file copied to safe location
  - [ ] Training curves saved
  - [ ] Validation metrics saved
  - [ ] Example predictions saved

- [ ] **Document findings**
  - [ ] Final mAP recorded
  - [ ] Per-class performance documented
  - [ ] Inference speed documented
  - [ ] Training time recorded
  - [ ] Hardware used noted (GPU/CPU)

- [ ] **Prepare for thesis**
  - [ ] Training methodology described
  - [ ] Results table prepared
  - [ ] Visualizations selected
  - [ ] Limitations identified

---

## Phase 9: Next Steps (Integration with Robot)

- [ ] **Optimize for ESP32**
  - [ ] Quantize model to INT8
  - [ ] Convert to TFLite Micro
  - [ ] Test on ESP32-CAM hardware

- [ ] **Real-world testing**
  - [ ] Deploy to robot
  - [ ] Test with classroom lighting
  - [ ] Measure end-to-end latency
  - [ ] Calculate sorting success rate

- [ ] **Fine-tune if needed**
  - [ ] Collect problematic examples
  - [ ] Add to training set
  - [ ] Re-train (Experiment 2)

---

## Troubleshooting Checklist

If something goes wrong, check:

- [ ] Python version is 3.8+
- [ ] All dependencies installed (`pip list`)
- [ ] Dataset paths are correct in `config.py`
- [ ] Sufficient disk space (>10GB free)
- [ ] Sufficient RAM (>8GB)
- [ ] No antivirus blocking file operations

**Common issues:**
- Out of memory → Reduce batch size in `config.py`
- Training too slow → Use GPU or reduce epochs
- Low mAP → Run Experiment 2 instead of 1
- Import errors → Re-run `setup_environment.py`

---

## Final Checklist

Before considering training complete:

- [ ] At least one model trained successfully
- [ ] Model meets success criteria (mAP ≥ 0.70)
- [ ] Model validated on test set
- [ ] Inference speed acceptable (<100ms)
- [ ] Model exported to TFLite
- [ ] Results documented
- [ ] Files backed up

---

## Results Summary Template

Fill this out after completing training:

**Experiment Used:** Experiment 1 / Experiment 2 / Experiment 3

**Hardware:**
- GPU: Yes / No (Model: _______________)
- RAM: ___________ GB
- CPU: _______________

**Training Time:**
- Stage 1: ___________ hours
- Stage 2: ___________ hours (if applicable)
- Total: ___________ hours

**Final Metrics:**
- mAP@0.5: ___________
- mAP@0.5:0.95: ___________
- Precision: ___________
- Recall: ___________
- F1 Score: ___________

**Per-Class Performance:**
- 1x1: ___________ AP
- 1x2: ___________ AP
- 2x2: ___________ AP
- 2x4: ___________ AP
- 2x6: ___________ AP
- 2x8: ___________ AP
- 2x10: ___________ AP
- 2x12: ___________ AP

**Inference Performance:**
- Average time: ___________ ms
- FPS: ___________
- Device: GPU / CPU

**Success Criteria:**
- [ ] mAP@0.5 ≥ 0.70
- [ ] Precision ≥ 0.75
- [ ] Recall ≥ 0.70
- [ ] Inference time ≤ 100ms

**Model Files:**
- Best model: `_______________________________________`
- Model size: ___________ MB
- TFLite export: `_______________________________________`

**Notes:**
_______________________________________________
_______________________________________________
_______________________________________________

---

**Date Started:** ___________________  
**Date Completed:** ___________________  
**Total Time:** ___________________

---

**Good luck with your training! 🎓🤖**
