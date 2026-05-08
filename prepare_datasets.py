#!/usr/bin/env python3
"""
Dataset Preparation Script for LEGO Object Detection
Handles:
- Scanning all dataset folders
- Converting annotations to YOLO format
- Mapping labels to target classes
- Removing duplicates and corrupted files
- Validating bounding boxes
- Splitting datasets (train/val/test)
- Generating dataset YAML files
"""

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple
import json
import hashlib
from collections import defaultdict

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm
import yaml

from config import (
    DATASET_DIR, PREPARED_DATA_DIR, TARGET_CLASSES, CLASS_TO_ID,
    LABEL_MAPPING, SPLIT_RATIOS, VALIDATION, SYNTHETIC_DATASET,
    SYNTHETIC_LABELS, REAL_WORLD_DATASET, REAL_WORLD_IMAGES
)


class DatasetPreparer:
    """Prepare and validate LEGO datasets for YOLOv8 training"""

    def __init__(self):
        self.stats = {
            "total_images": 0,
            "valid_images": 0,
            "corrupted_images": 0,
            "duplicate_images": 0,
            "total_annotations": 0,
            "valid_annotations": 0,
            "invalid_bboxes": 0,
            "unmapped_classes": set(),
            "class_distribution": defaultdict(int)
        }
        self.image_hashes = {}

    def compute_image_hash(self, image_path: Path) -> str:
        """Compute MD5 hash of image for duplicate detection"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            print(f"Error hashing {image_path}: {e}")
            return None

    def is_image_corrupted(self, image_path: Path) -> bool:
        """Check if image file is corrupted"""
        try:
            img = Image.open(image_path)
            img.verify()
            img = cv2.imread(str(image_path))
            if img is None:
                return True
            return False
        except Exception:
            return True

    def normalize_class_name(self, class_name: str) -> str:
        """Normalize class name using label mapping"""
        class_name = class_name.lower().strip()

        # Direct match
        if class_name in TARGET_CLASSES:
            return class_name

        # Check mapping
        if class_name in LABEL_MAPPING:
            return LABEL_MAPPING[class_name]

        # Try to extract size pattern (e.g., "3004 Brick 1x2" -> "1x2")
        for target in TARGET_CLASSES:
            if target in class_name or target.replace('x', ' x ') in class_name:
                return target

        return None

    def validate_bbox(self, bbox: List[float], img_width: int, img_height: int) -> bool:
        """Validate YOLO format bounding box"""
        x_center, y_center, width, height = bbox

        # Check if coordinates are within valid range [0, 1]
        if not (0 <= x_center <= 1 and 0 <= y_center <= 1):
            return False
        if not (0 < width <= 1 and 0 < height <= 1):
            return False

        # Check minimum area
        area = width * height * img_width * img_height
        if area < VALIDATION["min_bbox_area"]:
            return False

        # Check aspect ratio
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > VALIDATION["max_bbox_aspect_ratio"]:
            return False

        return True

    def convert_xml_to_yolo(self, xml_path: Path, image_path: Path) -> List[str]:
        """Convert Pascal VOC XML annotation to YOLO format"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            size = root.find('size')
            img_width = int(size.find('width').text)
            img_height = int(size.find('height').text)

            yolo_lines = []

            for obj in root.findall('object'):
                class_name = obj.find('name').text
                normalized_class = self.normalize_class_name(class_name)

                if normalized_class is None:
                    self.stats["unmapped_classes"].add(class_name)
                    continue

                if normalized_class not in TARGET_CLASSES:
                    continue

                class_id = CLASS_TO_ID[normalized_class]

                bndbox = obj.find('bndbox')
                xmin = float(bndbox.find('xmin').text)
                ymin = float(bndbox.find('ymin').text)
                xmax = float(bndbox.find('xmax').text)
                ymax = float(bndbox.find('ymax').text)

                # Convert to YOLO format (x_center, y_center, width, height) normalized
                x_center = (xmin + xmax) / 2 / img_width
                y_center = (ymin + ymax) / 2 / img_height
                width = (xmax - xmin) / img_width
                height = (ymax - ymin) / img_height

                bbox = [x_center, y_center, width, height]

                if not self.validate_bbox(bbox, img_width, img_height):
                    self.stats["invalid_bboxes"] += 1
                    continue

                yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
                self.stats["class_distribution"][normalized_class] += 1
                self.stats["valid_annotations"] += 1

            return yolo_lines

        except Exception as e:
            print(f"Error converting {xml_path}: {e}")
            return []

    def process_synthetic_dataset(self, output_dir: Path) -> List[Path]:
        """Process synthetic LEGO dataset (already in YOLO format)"""
        print("\n" + "="*60)
        print("Processing Synthetic Dataset")
        print("="*60)

        images_dir = output_dir / "images"
        labels_dir = output_dir / "labels"
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        valid_image_paths = []

        # Get all label files
        label_files = list(SYNTHETIC_LABELS.glob("*.txt"))
        print(f"Found {len(label_files)} label files")

        for label_path in tqdm(label_files, desc="Processing synthetic dataset"):
            # Find corresponding image
            image_name = label_path.stem.replace("image_", "") + ".jpg"
            image_path = SYNTHETIC_DATASET / f"{label_path.stem.replace('image_', '').zfill(5)}.jpg"

            if not image_path.exists():
                continue

            self.stats["total_images"] += 1

            # Check for corruption
            if VALIDATION["check_corrupted_images"] and self.is_image_corrupted(image_path):
                self.stats["corrupted_images"] += 1
                continue

            # Check for duplicates
            if VALIDATION["check_duplicate_images"]:
                img_hash = self.compute_image_hash(image_path)
                if img_hash in self.image_hashes:
                    self.stats["duplicate_images"] += 1
                    continue
                self.image_hashes[img_hash] = image_path

            # Process labels
            try:
                with open(label_path, 'r') as f:
                    lines = f.readlines()

                valid_lines = []
                img = cv2.imread(str(image_path))
                if img is None:
                    continue
                img_height, img_width = img.shape[:2]

                for line in lines:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue

                    class_id = int(float(parts[0]))
                    bbox = [float(x) for x in parts[1:5]]

                    # Map class ID to our target classes
                    # Note: Synthetic dataset class IDs may differ
                    # For now, we assume class 0 maps to our classes
                    # This needs to be adjusted based on actual dataset
                    if class_id < len(TARGET_CLASSES):
                        if self.validate_bbox(bbox, img_width, img_height):
                            valid_lines.append(line.strip())
                            self.stats["class_distribution"][TARGET_CLASSES[class_id]] += 1
                            self.stats["valid_annotations"] += 1

                if valid_lines:
                    # Copy image and label
                    new_image_path = images_dir / f"syn_{self.stats['valid_images']:06d}.jpg"
                    new_label_path = labels_dir / f"syn_{self.stats['valid_images']:06d}.txt"

                    shutil.copy(image_path, new_image_path)
                    with open(new_label_path, 'w') as f:
                        f.write('\n'.join(valid_lines))

                    valid_image_paths.append(new_image_path)
                    self.stats["valid_images"] += 1

            except Exception as e:
                print(f"Error processing {label_path}: {e}")
                continue

        print(f"✓ Processed {self.stats['valid_images']} valid synthetic images")
        return valid_image_paths

    def process_realworld_dataset(self, output_dir: Path) -> List[Path]:
        """Process real-world LEGO dataset (XML annotations)"""
        print("\n" + "="*60)
        print("Processing Real-World Dataset")
        print("="*60)

        images_dir = output_dir / "images"
        labels_dir = output_dir / "labels"
        images_dir.mkdir(parents=True, exist_ok=True)
        labels_dir.mkdir(parents=True, exist_ok=True)

        valid_image_paths = []
        xml_files = list(REAL_WORLD_DATASET.glob("*.xml"))
        print(f"Found {len(xml_files)} XML annotation files")

        start_idx = self.stats["valid_images"]

        for xml_path in tqdm(xml_files, desc="Processing real-world dataset"):
            image_name = xml_path.stem + ".jpg"
            image_path = REAL_WORLD_IMAGES / image_name

            if not image_path.exists():
                continue

            self.stats["total_images"] += 1

            # Check for corruption
            if VALIDATION["check_corrupted_images"] and self.is_image_corrupted(image_path):
                self.stats["corrupted_images"] += 1
                continue

            # Check for duplicates
            if VALIDATION["check_duplicate_images"]:
                img_hash = self.compute_image_hash(image_path)
                if img_hash in self.image_hashes:
                    self.stats["duplicate_images"] += 1
                    continue
                self.image_hashes[img_hash] = image_path

            # Convert XML to YOLO format
            yolo_lines = self.convert_xml_to_yolo(xml_path, image_path)

            if yolo_lines:
                new_image_path = images_dir / f"real_{self.stats['valid_images']:06d}.jpg"
                new_label_path = labels_dir / f"real_{self.stats['valid_images']:06d}.txt"

                shutil.copy(image_path, new_image_path)
                with open(new_label_path, 'w') as f:
                    f.write('\n'.join(yolo_lines))

                valid_image_paths.append(new_image_path)
                self.stats["valid_images"] += 1

        print(f"✓ Processed {self.stats['valid_images'] - start_idx} valid real-world images")
        return valid_image_paths

    def split_dataset(self, image_paths: List[Path], output_dir: Path):
        """Split dataset into train/val/test sets"""
        print("\n" + "="*60)
        print("Splitting Dataset")
        print("="*60)

        np.random.seed(42)
        np.random.shuffle(image_paths)

        n_train = int(len(image_paths) * SPLIT_RATIOS["train"])
        n_val = int(len(image_paths) * SPLIT_RATIOS["val"])

        train_images = image_paths[:n_train]
        val_images = image_paths[n_train:n_train + n_val]
        test_images = image_paths[n_train + n_val:]

        # Create split directories
        for split in ["train", "val", "test"]:
            (output_dir / split / "images").mkdir(parents=True, exist_ok=True)
            (output_dir / split / "labels").mkdir(parents=True, exist_ok=True)

        # Move files to respective splits
        splits = [
            ("train", train_images),
            ("val", val_images),
            ("test", test_images)
        ]

        for split_name, images in splits:
            print(f"\n{split_name.capitalize()} set: {len(images)} images")
            for img_path in tqdm(images, desc=f"Creating {split_name} set"):
                label_path = img_path.parent.parent / "labels" / (img_path.stem + ".txt")

                new_img_path = output_dir / split_name / "images" / img_path.name
                new_label_path = output_dir / split_name / "labels" / (img_path.stem + ".txt")

                shutil.move(str(img_path), str(new_img_path))
                if label_path.exists():
                    shutil.move(str(label_path), str(new_label_path))

        print(f"\n✓ Dataset split complete")
        print(f"  Train: {len(train_images)} ({SPLIT_RATIOS['train']*100:.0f}%)")
        print(f"  Val: {len(val_images)} ({SPLIT_RATIOS['val']*100:.0f}%)")
        print(f"  Test: {len(test_images)} ({SPLIT_RATIOS['test']*100:.0f}%)")

    def create_dataset_yaml(self, output_dir: Path, dataset_name: str):
        """Create YAML configuration file for YOLOv8"""
        yaml_content = {
            "path": str(output_dir.absolute()),
            "train": "train/images",
            "val": "val/images",
            "test": "test/images",
            "nc": len(TARGET_CLASSES),
            "names": TARGET_CLASSES
        }

        yaml_path = output_dir / "data.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)

        print(f"\n✓ Created {yaml_path}")
        return yaml_path

    def save_statistics(self, output_dir: Path):
        """Save dataset statistics"""
        stats_file = output_dir / "dataset_statistics.json"

        stats_output = {
            "total_images_scanned": self.stats["total_images"],
            "valid_images": self.stats["valid_images"],
            "corrupted_images": self.stats["corrupted_images"],
            "duplicate_images": self.stats["duplicate_images"],
            "total_annotations": self.stats["valid_annotations"],
            "invalid_bboxes": self.stats["invalid_bboxes"],
            "unmapped_classes": list(self.stats["unmapped_classes"]),
            "class_distribution": dict(self.stats["class_distribution"])
        }

        with open(stats_file, 'w') as f:
            json.dump(stats_output, f, indent=2)

        print(f"\n✓ Saved statistics to {stats_file}")

        # Print summary
        print("\n" + "="*60)
        print("Dataset Statistics")
        print("="*60)
        print(f"Total images scanned: {self.stats['total_images']}")
        print(f"Valid images: {self.stats['valid_images']}")
        print(f"Corrupted images: {self.stats['corrupted_images']}")
        print(f"Duplicate images: {self.stats['duplicate_images']}")
        print(f"Valid annotations: {self.stats['valid_annotations']}")
        print(f"Invalid bounding boxes: {self.stats['invalid_bboxes']}")
        print(f"\nClass Distribution:")
        for class_name in TARGET_CLASSES:
            count = self.stats["class_distribution"].get(class_name, 0)
            print(f"  {class_name}: {count}")
        if self.stats["unmapped_classes"]:
            print(f"\nUnmapped classes (ignored): {len(self.stats['unmapped_classes'])}")
            for cls in sorted(self.stats["unmapped_classes"]):
                print(f"  - {cls}")


def main():
    """Main dataset preparation workflow"""
    print("="*60)
    print("LEGO Object Detection - Dataset Preparation")
    print("="*60)

    preparer = DatasetPreparer()

    # Create output directory for each experiment
    for exp_num in [1, 2]:
        print(f"\n\n{'='*60}")
        print(f"Preparing Dataset for Experiment {exp_num}")
        print(f"{'='*60}")

        output_dir = PREPARED_DATA_DIR / f"experiment_{exp_num}"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Reset stats for each experiment
        preparer.stats = {
            "total_images": 0,
            "valid_images": 0,
            "corrupted_images": 0,
            "duplicate_images": 0,
            "total_annotations": 0,
            "valid_annotations": 0,
            "invalid_bboxes": 0,
            "unmapped_classes": set(),
            "class_distribution": defaultdict(int)
        }
        preparer.image_hashes = {}

        all_image_paths = []

        # Experiment 1: Synthetic only
        if exp_num == 1:
            all_image_paths.extend(preparer.process_synthetic_dataset(output_dir))

        # Experiment 2: Synthetic + Real-world
        elif exp_num == 2:
            all_image_paths.extend(preparer.process_synthetic_dataset(output_dir))
            all_image_paths.extend(preparer.process_realworld_dataset(output_dir))

        # Split dataset
        if all_image_paths:
            preparer.split_dataset(all_image_paths, output_dir)
            preparer.create_dataset_yaml(output_dir, f"experiment_{exp_num}")
            preparer.save_statistics(output_dir)

    print("\n" + "="*60)
    print("✓ Dataset preparation complete!")
    print("="*60)
    print("\nNext step:")
    print("Run training: python train.py --experiment 1")


if __name__ == "__main__":
    main()
