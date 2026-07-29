#!/usr/bin/env python3
"""Fine-tune the base detector on YOUR OWN webcam photos.

Two-stage transfer learning:
  Stage 1 (already done): train on the large pacogarciam3 dataset -> a base model
    that knows what each brick footprint looks like in general.
  Stage 2 (this script): continue training that base model on ~50-100 photos of
    YOUR bricks, taken with YOUR webcam at YOUR angle/lighting, so it adapts to
    your actual deployment conditions.

Because the base model already knows brick shapes, you need only a small dataset
here — you're teaching it your CONDITIONS, not the shapes from scratch. A low
learning rate + all layers unfrozen (FINETUNE_CONFIG) nudges it without erasing
what it learned.

Prerequisites:
  1. A base model from Stage 1 (e.g. training_output/.../best.pt, or models/lego_detector.pt).
  2. Your own labeled dataset in YOLO format with a data.yaml. Class names/order
     MUST match config.TARGET_CLASSES, or the class IDs won't line up.

Usage:
  python finetune_own.py --base models/lego_detector.pt --data my_photos/data.yaml
  # optional: --epochs 40 --out training_output/finetuned
On success it copies the new best.pt to models/lego_detector.pt and the running
backend picks it up on the next detection (detection.reload() / restart).
"""
import argparse
import shutil
from pathlib import Path

from config import FINETUNE_CONFIG, TARGET_CLASSES, MODEL_PATH


def _verify_classes(data_yaml: Path):
    """Warn loudly if the dataset's class names/order don't match config."""
    import yaml
    cfg = yaml.safe_load(data_yaml.read_text())
    names = cfg.get("names")
    if isinstance(names, dict):
        names = [names[k] for k in sorted(names, key=lambda x: int(x))]
    if list(names) != list(TARGET_CLASSES):
        print("=" * 60)
        print("WARNING: dataset class order does NOT match config.TARGET_CLASSES!")
        print(f"  dataset : {names}")
        print(f"  config  : {list(TARGET_CLASSES)}")
        print("  The fine-tuned model's class IDs will not line up with the rest")
        print("  of the system. Reorder your data.yaml names to match, then re-run.")
        print("=" * 60)
        return False
    print(f"Class check OK — {len(names)} classes, order matches config.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Base model .pt from Stage 1")
    ap.add_argument("--data", required=True, help="Your dataset's data.yaml")
    ap.add_argument("--epochs", type=int, default=FINETUNE_CONFIG.get("epochs", 50))
    ap.add_argument("--out", default="training_output/finetuned")
    ap.add_argument("--deploy", action="store_true",
                    help="Copy the resulting best.pt to models/lego_detector.pt")
    args = ap.parse_args()

    base = Path(args.base)
    data_yaml = Path(args.data)
    if not base.exists():
        raise SystemExit(f"Base model not found: {base}")
    if not data_yaml.exists():
        raise SystemExit(f"data.yaml not found: {data_yaml}")

    if not _verify_classes(data_yaml):
        raise SystemExit("Aborting due to class mismatch (see warning above).")

    from ultralytics import YOLO

    print(f"Loading base model: {base}")
    model = YOLO(str(base))

    # Fine-tune settings: unfreeze everything, low LR, fewer epochs (from config),
    # so the model gently adapts to your photos without forgetting brick shapes.
    ft = FINETUNE_CONFIG.copy()
    ft.update({
        "data": str(data_yaml),
        "epochs": args.epochs,
        "project": str(Path(args.out).parent),
        "name": Path(args.out).name,
        "exist_ok": True,
        "verbose": True,
        "plots": True,
    })
    ft.pop("model", None)  # model comes from the loaded checkpoint, not config

    print(f"Fine-tuning for {args.epochs} epochs at lr0={ft.get('lr0')}, freeze={ft.get('freeze')}")
    model.train(**ft)

    best = Path(args.out) / "weights" / "best.pt"
    if not best.exists():
        raise SystemExit(f"Training finished but no best.pt at {best}")
    print(f"\nFine-tuned model: {best}")

    if args.deploy:
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, MODEL_PATH)
        print(f"Deployed to {MODEL_PATH} — restart the backend (or it reloads on next detect).")
    else:
        print(f"To deploy: copy {best} -> {MODEL_PATH}, then restart the backend.")


if __name__ == "__main__":
    main()
