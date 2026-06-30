#!/usr/bin/env python3
"""
Detection health check.

Confirms the object-detection pipeline is functional end to end:
  1. A trained model is present and loads.
  2. The model's classes match config.TARGET_CLASSES.
  3. The model produces detections on a real test image.
  4. Detected classes map to sorting bins.

Run after dropping your trained best.pt at models/lego_detector.pt:

    python verify_detection.py
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config import get_model_path, TARGET_CLASSES, MODEL_PATH
from sorting_logic import LEGOSorter


def main():
    print("=" * 70)
    print("DETECTION HEALTH CHECK")
    print("=" * 70)

    # 1. Locate model
    model_path = get_model_path()
    if model_path is None:
        print("\n✗ No trained model found.")
        print(f"  Place your trained best.pt at: {MODEL_PATH}")
        print("  (e.g. copy experiment_2_*/stage2_finetuned/weights/best.pt from Drive)")
        return 1
    print(f"\n[1/4] Model found: {model_path}")

    # 2. Load model + check classes
    from ultralytics import YOLO
    model = YOLO(str(model_path))
    model_classes = sorted(model.names.values())
    expected = sorted(TARGET_CLASSES)
    print(f"[2/4] Model classes: {model_classes}")
    if model_classes != expected:
        print(f"  ⚠ WARNING: model classes do not match config.TARGET_CLASSES")
        print(f"    expected: {expected}")
        print("    Detection still runs, but sorting bins may not map. "
              "Update config.TARGET_CLASSES to match the model.")
    else:
        print("  ✓ Classes match config.TARGET_CLASSES")

    # 3. Run detection on a real image. Prefer the prepared test split, whose
    #    images are guaranteed to contain a labeled brick (raw datasets/images
    #    includes unannotated/empty frames that legitimately detect nothing).
    test_image = next(
        iter(sorted(Path("training_output/prepared_datasets/experiment_2/test/images").glob("*.jpg"))),
        None,
    )
    if test_image is None:
        test_image = next(iter(sorted(Path("datasets/images").glob("*.jpg"))), None)
    if test_image is None:
        print("\n✗ No test image available.")
        return 1

    print(f"[3/4] Running detection on: {test_image}")
    results = model(str(test_image), conf=0.25, verbose=False)
    boxes = results[0].boxes
    print(f"  Detections: {len(boxes)}")
    detected = []
    for box in boxes:
        cls = model.names[int(box.cls[0])]
        conf = float(box.conf[0])
        detected.append(cls)
        print(f"    - {cls}: {conf:.2f}")

    # 4. Map detected classes to bins
    print("[4/4] Sorting-bin mapping:")
    sorter = LEGOSorter()
    mapped_ok = True
    for cls in set(detected):
        try:
            bin_name, pos = sorter.get_target_bin(cls)
            print(f"    {cls} -> {bin_name} {pos}")
        except ValueError:
            mapped_ok = False
            print(f"    {cls} -> ⚠ no bin rule")

    print("\n" + "=" * 70)
    if len(boxes) == 0:
        print("RESULT: model loads and runs, but detected nothing on this image.")
        print("  If this is the trained model, try a different image or lower --conf.")
        print("  If this is the stale baseline model, drop in the real best.pt.")
        return 0
    print("RESULT: ✓ Detection pipeline is FUNCTIONAL"
          + ("" if mapped_ok else " (some classes lack bin rules)"))
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
