#!/usr/bin/env python3
"""
Threshold sweep: run inference once per sampled image, then re-threshold from
0.90 downward in 0.05 steps to see at what confidence cutoff (if any) overall
accuracy reaches 90%. Demonstrates whether lowering the threshold can recover
accuracy, given the model's failures are misclassifications vs. missed detections.
"""

import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import torch
from ultralytics import YOLO

from config import TARGET_CLASSES, get_model_path
from simulate_trials import collect_images_by_class

TRIALS_PER_CLASS = 10
SEED = 42
STEP = 0.05
FLOOR = 0.0
TARGET_ACC = 0.90


def main():
    random.seed(SEED)

    model_path = get_model_path()
    if model_path is None:
        print("No trained model found.")
        sys.exit(1)
    model = YOLO(str(model_path))
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    candidates = [
        Path("training_output/prepared_datasets/experiment_2/test"),
        Path("training_output/prepared_datasets/experiment_1/test"),
        Path("datasets/images"),
    ]
    image_root = next((p for p in candidates if p.exists()), None)
    by_class = collect_images_by_class(image_root)

    print(f"Model: {model_path}")
    print(f"Images: {image_root}  |  Device: {device}  |  Seed: {SEED}")
    print(f"Running inference once per image ({TRIALS_PER_CLASS} per class)...\n")

    # Run inference ONCE per sampled image; store (best_class, best_conf).
    stored = {}  # class -> [(best_cls, best_conf), ...]
    for cls in TARGET_CLASSES:
        if cls not in by_class:
            continue
        imgs = by_class[cls]
        pool = imgs * (TRIALS_PER_CLASS // len(imgs) + 1)
        sample = random.sample(pool, TRIALS_PER_CLASS)
        rows = []
        for img in sample:
            preds = model(str(img), conf=0.01, device=device, verbose=False)[0]
            best_cls, best_conf = None, 0.0
            for box in preds.boxes:
                cid = int(box.cls[0])
                cf = float(box.conf[0])
                if cid < len(TARGET_CLASSES) and cf > best_conf:
                    best_conf = cf
                    best_cls = TARGET_CLASSES[cid]
            rows.append((best_cls, best_conf))
        stored[cls] = rows

    classes = [c for c in TARGET_CLASSES if c in stored]

    # Sweep the threshold downward.
    print("=" * 78)
    print("THRESHOLD SWEEP — overall accuracy as confidence cutoff is lowered")
    print("=" * 78)
    header = f"{'Threshold':>10} | " + " ".join(f"{c.split('_')[0][0]}{c.split('_')[1]:>5}" for c in classes) + f" | {'Overall':>8}"
    print(header)
    print("-" * len(header))

    reached = None
    thr = 0.90
    while thr >= FLOOR - 1e-9:
        per_class = []
        total = correct = 0
        for cls in classes:
            c_correct = 0
            for best_cls, best_conf in stored[cls]:
                det = best_cls if best_conf >= thr else None
                if det == cls:
                    c_correct += 1
                    correct += 1
                total += 1
            per_class.append(c_correct)
        overall = correct / total if total else 0
        row = f"{thr:>10.2f} | " + " ".join(f"{pc:>6}" for pc in per_class) + f" | {overall:>7.0%}"
        print(row)
        if overall >= TARGET_ACC and reached is None:
            reached = (thr, overall)
            break
        thr = round(thr - STEP, 2)

    print("=" * 78)
    if reached:
        print(f"Reached {reached[1]:.0%} accuracy at threshold {reached[0]:.2f}")
    else:
        print(f"Accuracy NEVER reached {TARGET_ACC:.0%} even at threshold {FLOOR:.2f}.")
        # Show the ceiling: accuracy with threshold=0 (accept every top-1 detection)
        total = correct = 0
        for cls in classes:
            for best_cls, _ in stored[cls]:
                if best_cls == cls:
                    correct += 1
                total += 1
        print(f"Maximum possible accuracy (accept all top-1 detections): {correct/total:.0%}")
        print("Lowering the threshold cannot fix misclassification — the top-1")
        print("prediction is simply the wrong class for many trials.")


if __name__ == "__main__":
    main()
