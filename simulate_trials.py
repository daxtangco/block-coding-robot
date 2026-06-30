#!/usr/bin/env python3
"""
Simulated Detection Trials for LEGO Brick Classifier
Runs N inference trials per class and reports per-class accuracy,
confidence, and pass/fail against the thesis success criteria.

Usage:
    python simulate_trials.py                        # auto-discover model, use datasets/test
    python simulate_trials.py --images path/to/dir   # custom image folder
    python simulate_trials.py --trials 10            # N trials per class (default: 10)
    python simulate_trials.py --conf 0.90            # confidence threshold (default: 0.90)
"""

import argparse
import csv
import json
import random
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import torch
from ultralytics import YOLO

from config import TARGET_CLASSES, RESULTS_DIR, get_model_path

# ── success threshold (matches program-runner.js 90% gate) ──────────────────
DEFAULT_CONF = 0.90
TRIALS_PER_CLASS = 10

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def collect_images_by_class(root: Path) -> dict[str, list[Path]]:
    """
    Collect images from a YOLO-format dataset (images/ + labels/ siblings).
    Ground truth comes from the first class ID in the matching .txt label file.
    Falls back to folder name or filename if no label file exists.
    Returns {class_name: [path, ...]} — only classes with >=1 image.
    """
    by_class: dict[str, list[Path]] = {c: [] for c in TARGET_CLASSES}

    img_dir = root / "images" if (root / "images").exists() else root
    lbl_dir = root / "labels" if (root / "labels").exists() else None

    for p in img_dir.rglob("*"):
        if p.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        cls = None

        # 1. YOLO label file
        if lbl_dir:
            lbl_file = lbl_dir / (p.stem + ".txt")
            if lbl_file.exists():
                try:
                    first_line = lbl_file.read_text().strip().splitlines()[0]
                    class_id = int(first_line.split()[0])
                    if class_id < len(TARGET_CLASSES):
                        cls = TARGET_CLASSES[class_id]
                except Exception:
                    pass

        # 2. Parent folder name
        if cls is None:
            for part in p.parts:
                if part in by_class:
                    cls = part
                    break

        # 3. Filename substring
        if cls is None:
            stem = p.stem.lower()
            for c in TARGET_CLASSES:
                if c in stem:
                    cls = c
                    break

        if cls:
            by_class[cls].append(p)

    return {k: v for k, v in by_class.items() if v}


def run_trials(model: YOLO, images: list[Path], ground_truth: str,
               n_trials: int, conf_threshold: float, device: str) -> list[dict]:
    """
    Sample up to n_trials images (with replacement if fewer available),
    run inference on each, and return a list of trial result dicts.
    """
    pool = images * (n_trials // len(images) + 1)  # repeat to fill
    sample = random.sample(pool, n_trials)

    results = []
    for i, img_path in enumerate(sample, 1):
        preds = model(str(img_path), conf=0.01, device=device, verbose=False)[0]

        # Pick highest-confidence detection among TARGET_CLASSES
        best_cls, best_conf = None, 0.0
        for box in preds.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            if cls_id < len(TARGET_CLASSES) and conf > best_conf:
                best_conf = conf
                best_cls = TARGET_CLASSES[cls_id]

        detected = best_cls if best_conf >= conf_threshold else None
        correct = detected == ground_truth

        results.append({
            "trial": i,
            "ground_truth": ground_truth,
            "detected": detected or "none",
            "confidence": round(best_conf, 4),
            "threshold": conf_threshold,
            "pass": correct,
            "image": img_path.name,
        })

    return results


def summarise(trials: list[dict]) -> dict:
    n = len(trials)
    passed = sum(1 for t in trials if t["pass"])
    confs = [t["confidence"] for t in trials if t["detected"] != "none"]
    return {
        "trials": n,
        "correct": passed,
        "accuracy": round(passed / n, 4) if n else 0.0,
        "avg_confidence": round(sum(confs) / len(confs), 4) if confs else 0.0,
        "min_confidence": round(min(confs), 4) if confs else 0.0,
        "max_confidence": round(max(confs), 4) if confs else 0.0,
        "no_detection": sum(1 for t in trials if t["detected"] == "none"),
    }


def print_report(all_trials: dict[str, list[dict]], summaries: dict[str, dict],
                 conf_threshold: float):
    print("\n" + "=" * 70)
    print("SIMULATED DETECTION TRIALS — PER-CLASS SUMMARY")
    print(f"Confidence threshold: {conf_threshold:.0%}")
    print("=" * 70)

    header = f"{'Class':<14} {'Trials':>6} {'Correct':>7} {'Accuracy':>9} {'Avg Conf':>9} {'No Det':>7}"
    print(header)
    print("-" * 70)

    total_trials = total_correct = 0
    for cls in TARGET_CLASSES:
        if cls not in summaries:
            print(f"{cls:<14}  -- no images found --")
            continue
        s = summaries[cls]
        acc_str = f"{s['accuracy']:.0%}"
        conf_str = f"{s['avg_confidence']:.2f}"
        mark = "✓" if s["accuracy"] >= 0.80 else "✗"
        print(f"{cls:<14} {s['trials']:>6} {s['correct']:>7} {acc_str:>9} {conf_str:>9} {s['no_detection']:>7}  {mark}")
        total_trials += s["trials"]
        total_correct += s["correct"]

    print("-" * 70)
    overall = total_correct / total_trials if total_trials else 0
    print(f"{'OVERALL':<14} {total_trials:>6} {total_correct:>7} {overall:>9.0%}")
    print("=" * 70)


def save_csv(all_trials: dict[str, list[dict]], out_path: Path):
    rows = [t for trials in all_trials.values() for t in trials]
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n✓ Trial log saved to: {out_path}")


def save_json(summaries: dict[str, dict], out_path: Path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    print(f"✓ Summary JSON saved to: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Simulated per-class detection trials")
    parser.add_argument("--model", type=str, default=None,
                        help="Path to .pt model (auto-discovers if omitted)")
    parser.add_argument("--images", type=str, default=None,
                        help="Root folder with test images (uses datasets/ if omitted)")
    parser.add_argument("--trials", type=int, default=TRIALS_PER_CLASS,
                        help=f"Trials per class (default: {TRIALS_PER_CLASS})")
    parser.add_argument("--conf", type=float, default=DEFAULT_CONF,
                        help=f"Confidence threshold (default: {DEFAULT_CONF})")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    print("=" * 70)
    print("LEGO BRICK DETECTION — SIMULATED TRIALS")
    print("=" * 70)

    # Resolve model
    model_path = args.model
    if model_path is None:
        found = get_model_path()
        if found is None:
            print("\n✗ No trained model found. Place best.pt at models/lego_detector.pt")
            sys.exit(1)
        model_path = str(found)
        print(f"Model: {model_path}")

    model = YOLO(model_path)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    # Resolve image root
    if args.images:
        image_root = Path(args.images)
    else:
        # Try prepared test split first, fall back to raw datasets/images
        candidates = [
            Path("training_output/prepared_datasets/experiment_2/test"),
            Path("training_output/prepared_datasets/experiment_1/test"),
            Path("datasets/images"),
        ]
        image_root = next((p for p in candidates if p.exists()), None)
        if image_root is None:
            print("\n✗ No image directory found. Use --images path/to/folder")
            sys.exit(1)
        print(f"Images: {image_root}")

    by_class = collect_images_by_class(image_root)
    if not by_class:
        print(f"\n✗ No labelled images found under {image_root}")
        print("  Folder structure expected: <root>/<class_name>/<image.jpg>")
        print("  Or image filenames containing the class name.")
        sys.exit(1)

    print(f"\nFound images for: {', '.join(sorted(by_class))}")
    print(f"Trials per class: {args.trials}  |  Threshold: {args.conf:.0%}\n")

    # Run trials
    all_trials: dict[str, list[dict]] = {}
    summaries: dict[str, dict] = {}

    for cls in TARGET_CLASSES:
        if cls not in by_class:
            print(f"  {cls}: skipped (no images)")
            continue
        print(f"  {cls}: running {args.trials} trials...", end=" ", flush=True)
        trials = run_trials(model, by_class[cls], cls, args.trials, args.conf, device)
        all_trials[cls] = trials
        summaries[cls] = summarise(trials)
        s = summaries[cls]
        print(f"{s['correct']}/{s['trials']} correct ({s['accuracy']:.0%})")

    # Output
    print_report(all_trials, summaries, args.conf)

    out_dir = RESULTS_DIR / "trials"
    out_dir.mkdir(parents=True, exist_ok=True)
    save_csv(all_trials, out_dir / "trial_log.csv")
    save_json(summaries, out_dir / "trial_summary.json")

    print(f"\n{'=' * 70}")
    print("TRIALS COMPLETE")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
