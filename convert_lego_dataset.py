#!/usr/bin/env python3
"""Convert the pacogarciam3 "LEGO vs Generic Brick" CLASSIFICATION dataset into a
YOLO OBJECT-DETECTION dataset for our 6 footprint classes.

Why this works: that dataset ships one cropped, centred brick per image plus a CSV
(ImageKey.csv) giving each image's brick footprint. There are no bounding boxes, so
YOLO can't use it directly. Since every cropped image is a single centred brick, we
synthesise a full-frame bounding box per image (the brick fills most of the crop) and
emit YOLO-format labels + a train/val split + data.yaml.

Caveat (be honest in the thesis): the model learns "one centred brick fills the
frame," so it detects a single piece in the pickup zone well but is weaker on
scattered multi-brick scenes. That matches our single-piece-in-ROI workflow. For real
robustness, fine-tune afterwards on your own multi-brick photos.

Usage:
    python convert_lego_dataset.py --zip lego_dataset.zip --out datasets/lego_yolo
Then train, e.g. via the in-app Train Model tab (zip datasets/lego_yolo) or Colab.
"""
import argparse
import csv
import io
import random
import zipfile
from pathlib import Path

# Map the dataset's "Brick" column values -> our canonical class names (config.py
# TARGET_CLASSES). The dataset uses "2x2 L" (space); we standardise to "2x2_L".
CLASS_MAP = {
    "1x1": "1x1",
    "1x2": "1x2",
    "1x4": "1x4",
    "2x2": "2x2",
    "2x2 L": "2x2_L",
    "2x3": "2x3",
}

# Canonical class order — MUST match config.py TARGET_CLASSES so the trained model's
# class IDs line up with the rest of the system.
CLASS_ORDER = ["1x1", "1x2", "1x4", "2x2", "2x2_L", "2x3"]
CLASS_ID = {name: i for i, name in enumerate(CLASS_ORDER)}

# Full-frame box: brick is centred and fills most of the crop. 0.9x0.9 leaves a
# small margin so the box doesn't clip the brick edges.
BOX = "0.5 0.5 0.9 0.9"
VAL_FRACTION = 0.15
SEED = 42


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", required=True, help="Path to lego_dataset.zip")
    ap.add_argument("--out", default="datasets/lego_yolo", help="Output dataset dir")
    ap.add_argument("--limit-per-class", type=int, default=0,
                    help="Optional cap per class (0 = use all) — handy for a quick test run")
    args = ap.parse_args()

    out = Path(args.out)
    for split in ("train", "val"):
        (out / split / "images").mkdir(parents=True, exist_ok=True)
        (out / split / "labels").mkdir(parents=True, exist_ok=True)

    rng = random.Random(SEED)
    per_class_count = {c: 0 for c in CLASS_ORDER}
    written = {"train": 0, "val": 0}
    skipped_unmapped = 0

    with zipfile.ZipFile(args.zip) as z:
        # Build a lookup of every zip member by its basename, so we can find the
        # actual image file for a CSV row regardless of nested folder casing.
        members = {}
        for name in z.namelist():
            if name.lower().endswith((".jpg", ".jpeg", ".png")):
                members.setdefault(Path(name).name, name)

        # Read the CSV from inside the zip.
        with z.open("ImageKey.csv") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"))
            rows = list(reader)

        # Keep only cropped, single-brick, class-bearing rows.
        usable = []
        for r in rows:
            if r.get("Folder1", "").strip().lower() != "cropped images":
                continue
            brick = (r.get("Brick") or "").strip()
            if brick not in CLASS_MAP:
                if brick:
                    skipped_unmapped += 1
                continue
            usable.append((r.get("Image", "").strip(), CLASS_MAP[brick]))

        rng.shuffle(usable)

        for image_name, cls in usable:
            if args.limit_per_class and per_class_count[cls] >= args.limit_per_class:
                continue
            member = members.get(image_name)
            if not member:
                continue  # CSV references an image not present in this zip

            split = "val" if rng.random() < VAL_FRACTION else "train"
            # Copy the image out of the zip.
            data = z.read(member)
            (out / split / "images" / image_name).write_bytes(data)
            # Write its YOLO label (single full-frame box).
            label_name = Path(image_name).with_suffix(".txt").name
            (out / split / "labels" / label_name).write_text(f"{CLASS_ID[cls]} {BOX}\n")

            per_class_count[cls] += 1
            written[split] += 1

    # data.yaml — class order MUST equal CLASS_ORDER / config.TARGET_CLASSES.
    names_block = "\n".join(f"  {i}: {n}" for i, n in enumerate(CLASS_ORDER))
    (out / "data.yaml").write_text(
        f"path: {out.resolve()}\n"
        f"train: train/images\n"
        f"val: val/images\n"
        f"nc: {len(CLASS_ORDER)}\n"
        f"names:\n{names_block}\n"
    )

    print("=" * 60)
    print("Conversion complete.")
    print(f"  Output: {out.resolve()}")
    print(f"  Train images: {written['train']}   Val images: {written['val']}")
    print("  Per-class:")
    for c in CLASS_ORDER:
        print(f"    {c:6s}: {per_class_count[c]}")
    if skipped_unmapped:
        print(f"  Skipped rows with unmapped brick classes: {skipped_unmapped}")
    print(f"  data.yaml written with names order: {CLASS_ORDER}")
    print("=" * 60)
    print("Next: zip the output dir and upload via the Train Model tab, or point")
    print("      Colab/train.py at data.yaml. Verify the names order matches config.py.")


if __name__ == "__main__":
    main()
