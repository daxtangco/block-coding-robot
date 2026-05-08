#!/usr/bin/env python3
"""
Training Script for LEGO Object Detection
Handles all 3 experiments defined in PRD:
- Experiment 1: Synthetic only
- Experiment 2: Synthetic + Real-world fine-tuning
- Experiment 3: Optional extended training
"""

import argparse
import sys
from pathlib import Path
import torch
from ultralytics import YOLO
import yaml
from datetime import datetime

from config import (
    PREPARED_DATA_DIR, MODELS_DIR, RESULTS_DIR, LOGS_DIR,
    TRAIN_CONFIG, FINETUNE_CONFIG, EXPERIMENTS,
    PRETRAINED_MODEL, SUCCESS_CRITERIA, TENSORBOARD_LOG_DIR
)


class LEGOTrainer:
    """LEGO Object Detection Model Trainer"""

    def __init__(self, experiment_num: int):
        self.experiment_num = experiment_num
        self.experiment_config = EXPERIMENTS[experiment_num]
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Setup paths
        self.dataset_dir = PREPARED_DATA_DIR / f"experiment_{experiment_num}"
        self.data_yaml = self.dataset_dir / "data.yaml"
        self.output_dir = MODELS_DIR / f"experiment_{experiment_num}_{self.timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check if dataset exists
        if not self.data_yaml.exists():
            print(f"ERROR: Dataset not prepared for experiment {experiment_num}")
            print(f"Run: python prepare_datasets.py")
            sys.exit(1)

        # Device selection
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        if self.device == "cpu":
            print("WARNING: Training on CPU will be very slow")
            print("Consider using a machine with NVIDIA GPU")

    def train_stage1_synthetic(self):
        """Stage 1: Train on synthetic dataset (baseline)"""
        print("\n" + "="*60)
        print(f"Experiment {self.experiment_num} - Stage 1: Synthetic Baseline Training")
        print("="*60)

        # Initialize model
        model = YOLO(PRETRAINED_MODEL)

        # Training configuration
        train_args = TRAIN_CONFIG.copy()
        train_args.update({
            "data": str(self.data_yaml),
            "project": str(self.output_dir),
            "name": "stage1_synthetic",
            "exist_ok": True,
            "device": self.device,
            "verbose": True,
        })

        # Add TensorBoard logging
        train_args["plots"] = True

        print(f"\nTraining configuration:")
        print(f"  Model: {PRETRAINED_MODEL}")
        print(f"  Epochs: {train_args['epochs']}")
        print(f"  Batch size: {train_args['batch']}")
        print(f"  Image size: {train_args['imgsz']}")
        print(f"  Device: {self.device}")
        print(f"  Output: {self.output_dir / 'stage1_synthetic'}")

        # Train
        print("\nStarting training...")
        results = model.train(**train_args)

        print("\n✓ Stage 1 training complete")
        return model, results

    def train_stage2_finetune(self, pretrained_weights: Path):
        """Stage 2: Fine-tune on real-world dataset"""
        print("\n" + "="*60)
        print(f"Experiment {self.experiment_num} - Stage 2: Real-World Fine-Tuning")
        print("="*60)

        # Load model from Stage 1
        model = YOLO(str(pretrained_weights))

        # Fine-tuning configuration
        finetune_args = FINETUNE_CONFIG.copy()
        finetune_args.update({
            "data": str(self.data_yaml),
            "project": str(self.output_dir),
            "name": "stage2_finetuned",
            "exist_ok": True,
            "device": self.device,
            "verbose": True,
        })

        finetune_args["plots"] = True

        print(f"\nFine-tuning configuration:")
        print(f"  Starting from: {pretrained_weights}")
        print(f"  Epochs: {finetune_args['epochs']}")
        print(f"  Learning rate: {finetune_args['lr0']}")
        print(f"  Frozen layers: {finetune_args['freeze']}")

        # Fine-tune
        print("\nStarting fine-tuning...")
        results = model.train(**finetune_args)

        print("\n✓ Stage 2 fine-tuning complete")
        return model, results

    def validate_model(self, model: YOLO, stage_name: str):
        """Validate model on test set"""
        print("\n" + "="*60)
        print(f"Validating Model - {stage_name}")
        print("="*60)

        # Run validation
        results = model.val(
            data=str(self.data_yaml),
            split="test",
            save_json=True,
            plots=True
        )

        # Extract metrics
        metrics = {
            "mAP@0.5": results.box.map50,
            "mAP@0.5:0.95": results.box.map,
            "precision": results.box.mp,
            "recall": results.box.mr,
        }

        print(f"\nValidation Results:")
        print(f"  mAP@0.5: {metrics['mAP@0.5']:.4f}")
        print(f"  mAP@0.5:0.95: {metrics['mAP@0.5:0.95']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall: {metrics['recall']:.4f}")

        # Check success criteria
        print(f"\nSuccess Criteria Check:")
        passed = True
        if metrics['mAP@0.5'] >= SUCCESS_CRITERIA['min_mAP']:
            print(f"  ✓ mAP@0.5: {metrics['mAP@0.5']:.4f} >= {SUCCESS_CRITERIA['min_mAP']}")
        else:
            print(f"  ✗ mAP@0.5: {metrics['mAP@0.5']:.4f} < {SUCCESS_CRITERIA['min_mAP']}")
            passed = False

        if metrics['precision'] >= SUCCESS_CRITERIA['min_precision']:
            print(f"  ✓ Precision: {metrics['precision']:.4f} >= {SUCCESS_CRITERIA['min_precision']}")
        else:
            print(f"  ✗ Precision: {metrics['precision']:.4f} < {SUCCESS_CRITERIA['min_precision']}")
            passed = False

        if metrics['recall'] >= SUCCESS_CRITERIA['min_recall']:
            print(f"  ✓ Recall: {metrics['recall']:.4f} >= {SUCCESS_CRITERIA['min_recall']}")
        else:
            print(f"  ✗ Recall: {metrics['recall']:.4f} < {SUCCESS_CRITERIA['min_recall']}")
            passed = False

        if passed:
            print(f"\n✓ Model meets all success criteria!")
        else:
            print(f"\n✗ Model does not meet success criteria")
            print(f"   Consider: more training epochs, data augmentation, or model size")

        return metrics, passed

    def benchmark_inference(self, model: YOLO):
        """Benchmark inference speed"""
        print("\n" + "="*60)
        print("Benchmarking Inference Speed")
        print("="*60)

        # Get a test image
        test_images = list((self.dataset_dir / "test" / "images").glob("*.jpg"))
        if not test_images:
            print("No test images found")
            return

        test_image = test_images[0]

        # Warm-up
        for _ in range(5):
            _ = model(test_image, verbose=False)

        # Benchmark
        import time
        times = []
        n_runs = 50

        for _ in range(n_runs):
            start = time.time()
            _ = model(test_image, verbose=False)
            times.append((time.time() - start) * 1000)  # Convert to ms

        avg_time = sum(times) / len(times)
        fps = 1000 / avg_time

        print(f"\nInference Benchmark ({n_runs} runs):")
        print(f"  Average time: {avg_time:.2f} ms")
        print(f"  FPS: {fps:.2f}")

        if avg_time <= SUCCESS_CRITERIA['max_inference_time_ms']:
            print(f"  ✓ Inference time meets criteria (<= {SUCCESS_CRITERIA['max_inference_time_ms']} ms)")
        else:
            print(f"  ✗ Inference time exceeds criteria (> {SUCCESS_CRITERIA['max_inference_time_ms']} ms)")
            print(f"     Consider using a lighter model or optimization techniques")

        return avg_time, fps

    def run_experiment_1(self):
        """Run Experiment 1: Synthetic only"""
        print("\n" + "="*70)
        print(f"EXPERIMENT 1: {self.experiment_config['name']}")
        print(self.experiment_config['description'])
        print("="*70)

        # Stage 1: Train on synthetic
        model, results = self.train_stage1_synthetic()

        # Get best weights
        best_weights = self.output_dir / "stage1_synthetic" / "weights" / "best.pt"

        # Validate
        metrics, passed = self.validate_model(YOLO(str(best_weights)), "Experiment 1 - Synthetic Only")

        # Benchmark
        self.benchmark_inference(YOLO(str(best_weights)))

        print(f"\n{'='*70}")
        print(f"EXPERIMENT 1 COMPLETE")
        print(f"{'='*70}")
        print(f"Best model: {best_weights}")
        print(f"Results: {self.output_dir / 'stage1_synthetic'}")

        return best_weights, metrics, passed

    def run_experiment_2(self):
        """Run Experiment 2: Synthetic + Real-world fine-tuning"""
        print("\n" + "="*70)
        print(f"EXPERIMENT 2: {self.experiment_config['name']}")
        print(self.experiment_config['description'])
        print("="*70)

        # Stage 1: Train on synthetic
        model, results = self.train_stage1_synthetic()

        # Get Stage 1 best weights
        stage1_weights = self.output_dir / "stage1_synthetic" / "weights" / "best.pt"

        # Stage 2: Fine-tune on real-world
        model, results = self.train_stage2_finetune(stage1_weights)

        # Get final best weights
        best_weights = self.output_dir / "stage2_finetuned" / "weights" / "best.pt"

        # Validate
        metrics, passed = self.validate_model(YOLO(str(best_weights)), "Experiment 2 - Synthetic + Real-World")

        # Benchmark
        self.benchmark_inference(YOLO(str(best_weights)))

        print(f"\n{'='*70}")
        print(f"EXPERIMENT 2 COMPLETE")
        print(f"{'='*70}")
        print(f"Best model: {best_weights}")
        print(f"Results: {self.output_dir / 'stage2_finetuned'}")

        return best_weights, metrics, passed


def main():
    """Main training workflow"""
    parser = argparse.ArgumentParser(description="Train LEGO Object Detection Model")
    parser.add_argument("--experiment", type=int, choices=[1, 2, 3], required=True,
                        help="Experiment number (1: Synthetic only, 2: Synthetic + Real-world, 3: Extended)")
    args = parser.parse_args()

    print("="*70)
    print("LEGO OBJECT DETECTION - MODEL TRAINING")
    print("="*70)

    # Initialize trainer
    trainer = LEGOTrainer(args.experiment)

    # Run experiment
    if args.experiment == 1:
        best_weights, metrics, passed = trainer.run_experiment_1()
    elif args.experiment == 2:
        best_weights, metrics, passed = trainer.run_experiment_2()
    elif args.experiment == 3:
        print("\nExperiment 3 (Extended training with lego-brick-images)")
        print("This experiment requires annotation conversion for the optional dataset.")
        print("Not implemented yet - use Experiment 2 for best results.")
        sys.exit(0)

    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"\nBest model saved to: {best_weights}")
    print(f"\nTo use this model:")
    print(f"  from ultralytics import YOLO")
    print(f"  model = YOLO('{best_weights}')")
    print(f"  results = model('path/to/image.jpg')")
    print(f"\nTo view training logs in TensorBoard:")
    print(f"  tensorboard --logdir {trainer.output_dir}")


if __name__ == "__main__":
    main()
