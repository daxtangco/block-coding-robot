#!/usr/bin/env python3
"""
Validation Script for LEGO Object Detection Models
Provides detailed validation metrics and visualizations
"""

import argparse
from pathlib import Path
import json
import torch
from ultralytics import YOLO
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from config import PREPARED_DATA_DIR, RESULTS_DIR, TARGET_CLASSES


class ModelValidator:
    """Validate trained LEGO detection models"""

    def __init__(self, model_path: str, experiment_num: int):
        self.model_path = Path(model_path)
        self.experiment_num = experiment_num

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        # Load model
        print(f"Loading model: {self.model_path}")
        self.model = YOLO(str(self.model_path))

        # Dataset path
        self.dataset_dir = PREPARED_DATA_DIR / f"experiment_{experiment_num}"
        self.data_yaml = self.dataset_dir / "data.yaml"

        if not self.data_yaml.exists():
            raise FileNotFoundError(f"Dataset not found: {self.data_yaml}")

        # Output directory
        self.output_dir = RESULTS_DIR / f"validation_{self.model_path.stem}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Results will be saved to: {self.output_dir}")

    def run_validation(self, split="test"):
        """Run comprehensive validation"""
        print("\n" + "="*60)
        print(f"Running Validation on {split} set")
        print("="*60)

        results = self.model.val(
            data=str(self.data_yaml),
            split=split,
            save_json=True,
            save_hybrid=True,
            plots=True,
            verbose=True
        )

        # Extract metrics
        metrics = {
            "mAP@0.5": float(results.box.map50),
            "mAP@0.5:0.95": float(results.box.map),
            "precision": float(results.box.mp),
            "recall": float(results.box.mr),
            "F1": float(2 * (results.box.mp * results.box.mr) / (results.box.mp + results.box.mr + 1e-6))
        }

        # Per-class metrics
        per_class_ap = {}
        if hasattr(results.box, 'ap_class_index') and results.box.ap_class_index is not None:
            for idx, class_idx in enumerate(results.box.ap_class_index):
                if class_idx < len(TARGET_CLASSES):
                    class_name = TARGET_CLASSES[int(class_idx)]
                    per_class_ap[class_name] = float(results.box.ap[idx])

        metrics["per_class_AP"] = per_class_ap

        # Save metrics
        metrics_file = self.output_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)

        print(f"\n✓ Metrics saved to: {metrics_file}")

        return metrics, results

    def print_metrics_report(self, metrics):
        """Print formatted metrics report"""
        print("\n" + "="*60)
        print("VALIDATION METRICS REPORT")
        print("="*60)

        print(f"\nOverall Metrics:")
        print(f"  mAP@0.5:       {metrics['mAP@0.5']:.4f}")
        print(f"  mAP@0.5:0.95:  {metrics['mAP@0.5:0.95']:.4f}")
        print(f"  Precision:     {metrics['precision']:.4f}")
        print(f"  Recall:        {metrics['recall']:.4f}")
        print(f"  F1 Score:      {metrics['F1']:.4f}")

        if metrics.get("per_class_AP"):
            print(f"\nPer-Class Average Precision (AP@0.5):")
            for class_name, ap in sorted(metrics["per_class_AP"].items()):
                print(f"  {class_name:8s}: {ap:.4f}")

    def plot_per_class_performance(self, metrics):
        """Plot per-class AP as bar chart"""
        if not metrics.get("per_class_AP"):
            return

        plt.figure(figsize=(12, 6))
        classes = list(metrics["per_class_AP"].keys())
        aps = list(metrics["per_class_AP"].values())

        colors = ['green' if ap >= 0.7 else 'orange' if ap >= 0.5 else 'red' for ap in aps]

        plt.bar(classes, aps, color=colors, alpha=0.7, edgecolor='black')
        plt.axhline(y=0.7, color='green', linestyle='--', label='Target (0.70)')
        plt.xlabel('LEGO Brick Class', fontsize=12)
        plt.ylabel('Average Precision (AP@0.5)', fontsize=12)
        plt.title('Per-Class Detection Performance', fontsize=14, fontweight='bold')
        plt.ylim(0, 1.0)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()

        plot_file = self.output_dir / "per_class_performance.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Per-class performance plot saved to: {plot_file}")

    def create_metrics_summary_plot(self, metrics):
        """Create summary visualization of all key metrics"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Plot 1: Overall metrics radar chart
        categories = ['mAP@0.5', 'mAP@0.5:0.95', 'Precision', 'Recall', 'F1']
        values = [
            metrics['mAP@0.5'],
            metrics['mAP@0.5:0.95'],
            metrics['precision'],
            metrics['recall'],
            metrics['F1']
        ]

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        ax = plt.subplot(121, projection='polar')
        ax.plot(angles, values, 'o-', linewidth=2, label='Model Performance')
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.set_title('Overall Metrics', fontsize=12, fontweight='bold', pad=20)
        ax.grid(True)

        # Plot 2: Confusion indicators
        ax2 = axes[1]
        metric_names = ['mAP@0.5', 'Precision', 'Recall']
        metric_values = [metrics['mAP@0.5'], metrics['precision'], metrics['recall']]
        targets = [0.70, 0.75, 0.70]

        x = np.arange(len(metric_names))
        width = 0.35

        bars1 = ax2.bar(x - width/2, metric_values, width, label='Actual', color='skyblue', edgecolor='black')
        bars2 = ax2.bar(x + width/2, targets, width, label='Target', color='lightcoral', edgecolor='black')

        ax2.set_ylabel('Score', fontsize=11)
        ax2.set_title('Success Criteria Comparison', fontsize=12, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(metric_names)
        ax2.legend()
        ax2.set_ylim(0, 1.0)
        ax2.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        summary_file = self.output_dir / "metrics_summary.png"
        plt.savefig(summary_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Metrics summary plot saved to: {summary_file}")

    def generate_text_report(self, metrics):
        """Generate comprehensive text report"""
        report_file = self.output_dir / "validation_report.txt"

        with open(report_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("LEGO OBJECT DETECTION - VALIDATION REPORT\n")
            f.write("="*70 + "\n\n")

            f.write(f"Model: {self.model_path}\n")
            f.write(f"Experiment: {self.experiment_num}\n")
            f.write(f"Dataset: {self.data_yaml}\n\n")

            f.write("="*70 + "\n")
            f.write("OVERALL METRICS\n")
            f.write("="*70 + "\n\n")

            f.write(f"mAP@0.5:       {metrics['mAP@0.5']:.4f}\n")
            f.write(f"mAP@0.5:0.95:  {metrics['mAP@0.5:0.95']:.4f}\n")
            f.write(f"Precision:     {metrics['precision']:.4f}\n")
            f.write(f"Recall:        {metrics['recall']:.4f}\n")
            f.write(f"F1 Score:      {metrics['F1']:.4f}\n\n")

            f.write("="*70 + "\n")
            f.write("SUCCESS CRITERIA CHECK\n")
            f.write("="*70 + "\n\n")

            criteria = [
                ("mAP@0.5", metrics['mAP@0.5'], 0.70),
                ("Precision", metrics['precision'], 0.75),
                ("Recall", metrics['recall'], 0.70)
            ]

            all_passed = True
            for name, value, target in criteria:
                status = "PASS ✓" if value >= target else "FAIL ✗"
                f.write(f"{name:12s}: {value:.4f} / {target:.2f} [{status}]\n")
                if value < target:
                    all_passed = False

            f.write(f"\nOverall Status: {'PASSED ✓' if all_passed else 'FAILED ✗'}\n\n")

            if metrics.get("per_class_AP"):
                f.write("="*70 + "\n")
                f.write("PER-CLASS PERFORMANCE\n")
                f.write("="*70 + "\n\n")

                for class_name, ap in sorted(metrics["per_class_AP"].items()):
                    f.write(f"{class_name:8s}: {ap:.4f}\n")

            f.write("\n" + "="*70 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*70 + "\n")

        print(f"✓ Text report saved to: {report_file}")


def main():
    """Main validation workflow"""
    parser = argparse.ArgumentParser(description="Validate LEGO Object Detection Model")
    parser.add_argument("--model", type=str, required=True,
                        help="Path to trained model weights (.pt file)")
    parser.add_argument("--experiment", type=int, choices=[1, 2, 3], required=True,
                        help="Experiment number used for training")
    parser.add_argument("--split", type=str, default="test", choices=["train", "val", "test"],
                        help="Dataset split to validate on")
    args = parser.parse_args()

    print("="*70)
    print("LEGO OBJECT DETECTION - MODEL VALIDATION")
    print("="*70)

    # Initialize validator
    validator = ModelValidator(args.model, args.experiment)

    # Run validation
    metrics, results = validator.run_validation(args.split)

    # Generate reports and visualizations
    validator.print_metrics_report(metrics)
    validator.plot_per_class_performance(metrics)
    validator.create_metrics_summary_plot(metrics)
    validator.generate_text_report(metrics)

    print("\n" + "="*70)
    print("VALIDATION COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {validator.output_dir}")


if __name__ == "__main__":
    main()
