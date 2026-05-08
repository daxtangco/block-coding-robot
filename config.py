"""
Configuration file for LEGO Object Detection Training
Contains all paths, hyperparameters, and settings defined in PRD
"""

import os
from pathlib import Path

# ============================================================================
# PROJECT PATHS
# ============================================================================

# Root directory
ROOT_DIR = Path(__file__).parent.absolute()

# Dataset paths
DATASET_DIR = ROOT_DIR / "datasets"
SYNTHETIC_DATASET = DATASET_DIR / "images"  # synthetic-lego-brick-dataset
SYNTHETIC_LABELS = DATASET_DIR / "YOLO_ready_txt_labels"
REAL_WORLD_DATASET = DATASET_DIR / "annotations"  # spiled-lego-bricks (XML format)
REAL_WORLD_IMAGES = DATASET_DIR / "images"
OPTIONAL_DATASET = DATASET_DIR / "LEGO brick images v1"  # lego-brick-images

# Output paths
OUTPUT_DIR = ROOT_DIR / "training_output"
PREPARED_DATA_DIR = OUTPUT_DIR / "prepared_datasets"
MODELS_DIR = OUTPUT_DIR / "models"
RESULTS_DIR = OUTPUT_DIR / "results"
LOGS_DIR = OUTPUT_DIR / "logs"

# Create output directories
for directory in [OUTPUT_DIR, PREPARED_DATA_DIR, MODELS_DIR, RESULTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# TARGET CLASSES (Updated to match available dataset)
# ============================================================================

# Original PRD classes (unavailable in current dataset):
# ["1x1", "1x2", "2x2", "2x4", "2x6", "2x8", "2x10", "2x12"]

# Updated to match real-world dataset (spiled-lego-bricks)
TARGET_CLASSES = [
    "brick_1x6",
    "brick_2x2",
    "brick_2x4",
    "plate_1x2",
    "plate_2x2",
    "plate_2x4"
]

# Class ID mapping
CLASS_TO_ID = {class_name: idx for idx, class_name in enumerate(TARGET_CLASSES)}
ID_TO_CLASS = {idx: class_name for class_name, idx in CLASS_TO_ID.items()}

# ============================================================================
# LABEL MAPPING (normalize different label formats to target classes)
# ============================================================================

LABEL_MAPPING = {
    # Normalize naming variations
    "brick 1x6": "brick_1x6",
    "brick_1x6": "brick_1x6",
    "1x6": "brick_1x6",

    "brick 2x2": "brick_2x2",
    "brick_2x2": "brick_2x2",
    "2x2": "brick_2x2",
    "3003": "brick_2x2",
    "3003 brick 2x2": "brick_2x2",

    "brick 2x4": "brick_2x4",
    "brick_2x4": "brick_2x4",
    "2x4": "brick_2x4",
    "3001": "brick_2x4",
    "3001 brick 2x4": "brick_2x4",

    "plate 1x2": "plate_1x2",
    "plate_1x2": "plate_1x2",
    "1x2": "plate_1x2",

    "plate 2x2": "plate_2x2",
    "plate_2x2": "plate_2x2",

    "plate 2x4": "plate_2x4",
    "plate_2x4": "plate_2x4",
}

# ============================================================================
# MODEL CONFIGURATION
# ============================================================================

# Starting model (from PRD)
PRETRAINED_MODEL = "yolov8n.pt"  # Lightweight, fast, suitable for education
ALTERNATIVE_MODELS = ["yolov8s.pt", "yolov8m.pt"]  # Optional upgrades

# ============================================================================
# TRAINING PARAMETERS (from PRD)
# ============================================================================

TRAIN_CONFIG = {
    # Core parameters
    "model": PRETRAINED_MODEL,
    "epochs": 100,
    "batch": 16,
    "imgsz": 640,
    "patience": 20,
    "optimizer": "AdamW",
    "pretrained": True,
    "seed": 42,
    "deterministic": True,
    "workers": 8,
    "save": True,
    "save_period": 10,
    "cache": True,
    "amp": True,  # Automatic Mixed Precision

    # Learning rate parameters
    "lr0": 0.001,
    "lrf": 0.01,
    "momentum": 0.937,
    "weight_decay": 0.0005,
    "warmup_epochs": 3,
    "warmup_momentum": 0.8,
    "warmup_bias_lr": 0.1,
    "cos_lr": True,

    # Layer freezing
    "freeze": 10,  # Freeze first 10 layers initially

    # Loss function parameters
    "box": 7.5,
    "cls": 0.5,
    "dfl": 1.5,

    # Data augmentation
    "mosaic": 1.0,
    "mixup": 0.0,
    "cutmix": 0.0,
    "fliplr": 0.5,
    "flipud": 0.0,
    "degrees": 0.0,
    "translate": 0.1,
    "scale": 0.5,
    "shear": 0.0,
    "perspective": 0.0,
    "hsv_h": 0.015,
    "hsv_s": 0.7,
    "hsv_v": 0.4,
    "close_mosaic": 10,
}

# Fine-tuning configuration (for Stage 2)
FINETUNE_CONFIG = TRAIN_CONFIG.copy()
FINETUNE_CONFIG.update({
    "freeze": 0,  # Unfreeze all layers for fine-tuning
    "epochs": 50,  # Fewer epochs for fine-tuning
    "lr0": 0.0001,  # Lower learning rate
})

# ============================================================================
# DATASET SPLIT RATIOS (from PRD)
# ============================================================================

SPLIT_RATIOS = {
    "train": 0.70,
    "val": 0.15,
    "test": 0.15
}

# ============================================================================
# EVALUATION METRICS (from PRD)
# ============================================================================

METRICS_TO_TRACK = [
    "mAP@0.5",
    "mAP@0.5:0.95",
    "precision",
    "recall",
    "F1",
    "per_class_AP",
    "confusion_matrix",
    "inference_time",
    "FPS"
]

# ============================================================================
# SUCCESS CRITERIA (from PRD)
# ============================================================================

SUCCESS_CRITERIA = {
    "min_mAP": 0.70,
    "min_precision": 0.75,
    "min_recall": 0.70,
    "max_inference_time_ms": 100,  # For real-time operation
}

# ============================================================================
# EXPERIMENT CONFIGURATIONS
# ============================================================================

EXPERIMENTS = {
    1: {
        "name": "Synthetic Only",
        "description": "Train only on synthetic dataset",
        "datasets": ["synthetic"],
        "config": TRAIN_CONFIG,
    },
    2: {
        "name": "Synthetic + Real-World",
        "description": "Train on synthetic, fine-tune on real-world",
        "datasets": ["synthetic", "real_world"],
        "config": FINETUNE_CONFIG,
    },
    3: {
        "name": "Optional Extended Training",
        "description": "Include lego-brick-images if annotations available",
        "datasets": ["synthetic", "real_world", "optional"],
        "config": FINETUNE_CONFIG,
    }
}

# ============================================================================
# VALIDATION SETTINGS
# ============================================================================

VALIDATION = {
    "check_corrupted_images": True,
    "check_duplicate_images": True,
    "validate_bounding_boxes": True,
    "min_bbox_area": 100,  # Minimum bounding box area in pixels
    "max_bbox_aspect_ratio": 10,  # Maximum aspect ratio (width/height)
}

# ============================================================================
# HARDWARE SETTINGS
# ============================================================================

# Will be auto-detected during training
DEVICE = "cuda:0"  # Will fallback to "cpu" if CUDA not available

# ============================================================================
# TENSORBOARD SETTINGS
# ============================================================================

TENSORBOARD_ENABLED = True
TENSORBOARD_LOG_DIR = LOGS_DIR / "tensorboard"
TENSORBOARD_LOG_DIR.mkdir(parents=True, exist_ok=True)
