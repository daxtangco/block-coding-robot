#!/usr/bin/env python3
"""
Thesis Results Visualization Generator
Creates publication-quality graphs for thesis results and comparison section
"""

import argparse
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List

from config import TARGET_CLASSES, RESULTS_DIR


class ThesisGraphGenerator:
    """Generate comprehensive graphs for thesis results section"""

    def __init__(self, output_dir: Path = None):
        if output_dir is None:
            self.output_dir = RESULTS_DIR / "thesis_graphs"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set publication style
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['legend.fontsize'] = 10
        plt.rcParams['figure.dpi'] = 300

        print(f"Thesis graphs will be saved to: {self.output_dir}")

    def load_training_results(self, results_csv_path: Path) -> pd.DataFrame:
        """Load training results.csv from YOLOv8 output"""
        if not results_csv_path.exists():
            raise FileNotFoundError(f"Results file not found: {results_csv_path}")

        df = pd.read_csv(results_csv_path)
        # Clean column names (remove leading/trailing spaces)
        df.columns = df.columns.str.strip()
        return df

    def load_validation_metrics(self, metrics_json_path: Path) -> Dict:
        """Load validation metrics JSON"""
        if not metrics_json_path.exists():
            raise FileNotFoundError(f"Metrics file not found: {metrics_json_path}")

        with open(metrics_json_path, 'r') as f:
            return json.load(f)

    def plot_training_curves_combined(self, experiment_results: Dict[str, Path]):
        """
        Graph 1: Training Loss Curves Comparison
        Compare training/validation loss across experiments
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        for idx, (exp_name, results_path) in enumerate(experiment_results.items()):
            df = self.load_training_results(results_path)
            color = colors[idx]

            # Box loss
            axes[0, 0].plot(df['epoch'], df['train/box_loss'],
                           label=f'{exp_name} (train)', color=color, linewidth=2)
            axes[0, 0].plot(df['epoch'], df['val/box_loss'],
                           label=f'{exp_name} (val)', color=color, linewidth=2, linestyle='--')

            # Class loss
            axes[0, 1].plot(df['epoch'], df['train/cls_loss'],
                           label=f'{exp_name} (train)', color=color, linewidth=2)
            axes[0, 1].plot(df['epoch'], df['val/cls_loss'],
                           label=f'{exp_name} (val)', color=color, linewidth=2, linestyle='--')

            # DFL loss
            axes[1, 0].plot(df['epoch'], df['train/dfl_loss'],
                           label=f'{exp_name} (train)', color=color, linewidth=2)
            axes[1, 0].plot(df['epoch'], df['val/dfl_loss'],
                           label=f'{exp_name} (val)', color=color, linewidth=2, linestyle='--')

            # Total loss (if available)
            if 'train/loss' in df.columns:
                axes[1, 1].plot(df['epoch'], df['train/loss'],
                               label=f'{exp_name} (train)', color=color, linewidth=2)
                axes[1, 1].plot(df['epoch'], df['val/loss'],
                               label=f'{exp_name} (val)', color=color, linewidth=2, linestyle='--')

        # Configure subplots
        axes[0, 0].set_title('Box Loss (Localization)', fontweight='bold')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(alpha=0.3)

        axes[0, 1].set_title('Classification Loss', fontweight='bold')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('Loss')
        axes[0, 1].legend()
        axes[0, 1].grid(alpha=0.3)

        axes[1, 0].set_title('DFL Loss (Distribution Focal Loss)', fontweight='bold')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('Loss')
        axes[1, 0].legend()
        axes[1, 0].grid(alpha=0.3)

        axes[1, 1].set_title('Total Loss', fontweight='bold')
        axes[1, 1].set_xlabel('Epoch')
        axes[1, 1].set_ylabel('Loss')
        axes[1, 1].legend()
        axes[1, 1].grid(alpha=0.3)

        plt.suptitle('Training Loss Curves Comparison Across Experiments',
                     fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()

        output_path = self.output_dir / "fig1_training_loss_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Graph 1: Training loss comparison saved to {output_path}")

    def plot_map_progression(self, experiment_results: Dict[str, Path]):
        """
        Graph 2: mAP Progression During Training
        Show how mAP@0.5 and mAP@0.5:0.95 improve across epochs
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        for idx, (exp_name, results_path) in enumerate(experiment_results.items()):
            df = self.load_training_results(results_path)
            color = colors[idx]

            # mAP@0.5
            if 'metrics/mAP50(B)' in df.columns:
                axes[0].plot(df['epoch'], df['metrics/mAP50(B)'],
                           label=exp_name, color=color, linewidth=2.5, marker='o',
                           markevery=10, markersize=4)

            # mAP@0.5:0.95
            if 'metrics/mAP50-95(B)' in df.columns:
                axes[1].plot(df['epoch'], df['metrics/mAP50-95(B)'],
                           label=exp_name, color=color, linewidth=2.5, marker='s',
                           markevery=10, markersize=4)

        # Target line
        axes[0].axhline(y=0.70, color='red', linestyle='--', linewidth=2,
                       label='Target (0.70)', alpha=0.7)

        # Configure subplots
        axes[0].set_title('mAP@0.5 Progression', fontweight='bold', fontsize=14)
        axes[0].set_xlabel('Epoch', fontsize=12)
        axes[0].set_ylabel('mAP@0.5', fontsize=12)
        axes[0].legend(loc='lower right')
        axes[0].grid(alpha=0.3)
        axes[0].set_ylim(0, 1.0)

        axes[1].set_title('mAP@0.5:0.95 Progression', fontweight='bold', fontsize=14)
        axes[1].set_xlabel('Epoch', fontsize=12)
        axes[1].set_ylabel('mAP@0.5:0.95', fontsize=12)
        axes[1].legend(loc='lower right')
        axes[1].grid(alpha=0.3)
        axes[1].set_ylim(0, 1.0)

        plt.suptitle('Model Performance (mAP) Across Training Epochs',
                     fontsize=16, fontweight='bold')
        plt.tight_layout()

        output_path = self.output_dir / "fig2_map_progression.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Graph 2: mAP progression saved to {output_path}")

    def plot_precision_recall_curves(self, experiment_results: Dict[str, Path]):
        """
        Graph 3: Precision and Recall Progression
        Show P/R balance across training
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        for idx, (exp_name, results_path) in enumerate(experiment_results.items()):
            df = self.load_training_results(results_path)
            color = colors[idx]

            # Precision
            if 'metrics/precision(B)' in df.columns:
                axes[0].plot(df['epoch'], df['metrics/precision(B)'],
                           label=exp_name, color=color, linewidth=2.5)

            # Recall
            if 'metrics/recall(B)' in df.columns:
                axes[1].plot(df['epoch'], df['metrics/recall(B)'],
                           label=exp_name, color=color, linewidth=2.5)

        # Target lines
        axes[0].axhline(y=0.75, color='red', linestyle='--', linewidth=2,
                       label='Target (0.75)', alpha=0.7)
        axes[1].axhline(y=0.70, color='red', linestyle='--', linewidth=2,
                       label='Target (0.70)', alpha=0.7)

        # Configure subplots
        axes[0].set_title('Precision Progression', fontweight='bold', fontsize=14)
        axes[0].set_xlabel('Epoch', fontsize=12)
        axes[0].set_ylabel('Precision', fontsize=12)
        axes[0].legend(loc='lower right')
        axes[0].grid(alpha=0.3)
        axes[0].set_ylim(0, 1.0)

        axes[1].set_title('Recall Progression', fontweight='bold', fontsize=14)
        axes[1].set_xlabel('Epoch', fontsize=12)
        axes[1].set_ylabel('Recall', fontsize=12)
        axes[1].legend(loc='lower right')
        axes[1].grid(alpha=0.3)
        axes[1].set_ylim(0, 1.0)

        plt.suptitle('Precision and Recall Across Training Epochs',
                     fontsize=16, fontweight='bold')
        plt.tight_layout()

        output_path = self.output_dir / "fig3_precision_recall_progression.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Graph 3: Precision/Recall progression saved to {output_path}")

    def plot_final_metrics_comparison(self, experiment_metrics: Dict[str, Dict]):
        """
        Graph 4: Final Metrics Comparison Bar Chart
        Compare final performance across experiments
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        experiments = list(experiment_metrics.keys())
        metrics_names = ['mAP@0.5', 'mAP@0.5:0.95', 'Precision', 'Recall', 'F1']

        x = np.arange(len(experiments))
        width = 0.15

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

        for i, metric in enumerate(metrics_names):
            values = [experiment_metrics[exp].get(metric, 0) for exp in experiments]
            ax.bar(x + i*width, values, width, label=metric, color=colors[i],
                   edgecolor='black', linewidth=1)

        # Target lines
        ax.axhline(y=0.70, color='red', linestyle='--', linewidth=1.5,
                  alpha=0.5, label='Target (0.70)')
        ax.axhline(y=0.75, color='orange', linestyle='--', linewidth=1.5,
                  alpha=0.5, label='Target (0.75)')

        ax.set_xlabel('Experiment', fontsize=12, fontweight='bold')
        ax.set_ylabel('Score', fontsize=12, fontweight='bold')
        ax.set_title('Final Model Performance Comparison Across Experiments',
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * 2)
        ax.set_xticklabels(experiments)
        ax.legend(loc='upper left', ncol=2)
        ax.set_ylim(0, 1.0)
        ax.grid(axis='y', alpha=0.3)

        # Add value labels on bars
        for i, metric in enumerate(metrics_names):
            values = [experiment_metrics[exp].get(metric, 0) for exp in experiments]
            for j, v in enumerate(values):
                ax.text(j + i*width, v + 0.02, f'{v:.2f}',
                       ha='center', va='bottom', fontsize=8, fontweight='bold')

        plt.tight_layout()

        output_path = self.output_dir / "fig4_final_metrics_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Graph 4: Final metrics comparison saved to {output_path}")

    def plot_per_class_comparison(self, experiment_metrics: Dict[str, Dict]):
        """
        Graph 5: Per-Class AP Comparison
        Compare per-class performance across experiments
        """
        fig, ax = plt.subplots(figsize=(14, 6))

        experiments = list(experiment_metrics.keys())
        classes = TARGET_CLASSES

        x = np.arange(len(classes))
        width = 0.8 / len(experiments)

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

        for i, exp in enumerate(experiments):
            per_class_ap = experiment_metrics[exp].get('per_class_AP', {})
            values = [per_class_ap.get(cls, 0) for cls in classes]

            ax.bar(x + i*width, values, width, label=exp, color=colors[i],
                   edgecolor='black', linewidth=0.8)

        # Target line
        ax.axhline(y=0.70, color='red', linestyle='--', linewidth=2,
                  label='Target (0.70)', alpha=0.7)

        ax.set_xlabel('LEGO Brick Class', fontsize=12, fontweight='bold')
        ax.set_ylabel('Average Precision (AP@0.5)', fontsize=12, fontweight='bold')
        ax.set_title('Per-Class Detection Performance Comparison',
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * (len(experiments) - 1) / 2)
        ax.set_xticklabels(classes, rotation=0)
        ax.legend(loc='upper left')
        ax.set_ylim(0, 1.0)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        output_path = self.output_dir / "fig5_per_class_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Graph 5: Per-class comparison saved to {output_path}")

    def plot_inference_speed_comparison(self, inference_data: Dict[str, Dict]):
        """
        Graph 6: Inference Speed Comparison
        Compare inference time and FPS across experiments/devices
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        experiments = list(inference_data.keys())

        inference_times = [inference_data[exp]['avg_ms'] for exp in experiments]
        fps_values = [inference_data[exp]['fps'] for exp in experiments]

        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']

        # Inference time
        bars1 = axes[0].bar(experiments, inference_times, color=colors[:len(experiments)],
                           edgecolor='black', linewidth=1.5, alpha=0.8)
        axes[0].axhline(y=100, color='red', linestyle='--', linewidth=2,
                       label='Target (≤100ms)', alpha=0.7)
        axes[0].set_ylabel('Inference Time (ms)', fontsize=12, fontweight='bold')
        axes[0].set_title('Average Inference Time', fontsize=14, fontweight='bold')
        axes[0].legend()
        axes[0].grid(axis='y', alpha=0.3)

        # Add value labels
        for bar, value in zip(bars1, inference_times):
            height = bar.get_height()
            axes[0].text(bar.get_x() + bar.get_width()/2., height + 2,
                        f'{value:.1f}ms', ha='center', va='bottom',
                        fontweight='bold', fontsize=10)

        # FPS
        bars2 = axes[1].bar(experiments, fps_values, color=colors[:len(experiments)],
                           edgecolor='black', linewidth=1.5, alpha=0.8)
        axes[1].axhline(y=10, color='green', linestyle='--', linewidth=2,
                       label='Target (≥10 FPS)', alpha=0.7)
        axes[1].set_ylabel('Frames Per Second (FPS)', fontsize=12, fontweight='bold')
        axes[1].set_title('Inference Speed (FPS)', fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(axis='y', alpha=0.3)

        # Add value labels
        for bar, value in zip(bars2, fps_values):
            height = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{value:.1f}', ha='center', va='bottom',
                        fontweight='bold', fontsize=10)

        plt.suptitle('Inference Performance Comparison',
                     fontsize=16, fontweight='bold')
        plt.tight_layout()

        output_path = self.output_dir / "fig6_inference_speed_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Graph 6: Inference speed comparison saved to {output_path}")

    def plot_success_criteria_dashboard(self, experiment_metrics: Dict[str, Dict]):
        """
        Graph 7: Success Criteria Dashboard
        Visual summary showing which experiments meet success criteria
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        experiments = list(experiment_metrics.keys())
        criteria = [
            ('mAP@0.5', 0.70),
            ('Precision', 0.75),
            ('Recall', 0.70)
        ]

        # Create grid
        y_pos = np.arange(len(experiments))
        x_pos = np.arange(len(criteria))

        # Create heatmap data
        heatmap_data = []
        annotations = []

        for exp in experiments:
            row = []
            ann_row = []
            for metric, target in criteria:
                value = experiment_metrics[exp].get(metric, 0)
                passes = value >= target
                row.append(value)
                ann_row.append(f'{value:.3f}\n{"✓ PASS" if passes else "✗ FAIL"}')
            heatmap_data.append(row)
            annotations.append(ann_row)

        # Plot heatmap
        im = ax.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=0.5, vmax=1.0)

        # Set ticks
        ax.set_xticks(x_pos)
        ax.set_yticks(y_pos)
        ax.set_xticklabels([f'{m}\n(≥{t})' for m, t in criteria], fontsize=11)
        ax.set_yticklabels(experiments, fontsize=11)

        # Add text annotations
        for i in range(len(experiments)):
            for j in range(len(criteria)):
                text = ax.text(j, i, annotations[i][j],
                              ha="center", va="center", color="black",
                              fontweight='bold', fontsize=10)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Metric Value', rotation=270, labelpad=20, fontsize=11)

        ax.set_title('Success Criteria Evaluation Dashboard',
                    fontsize=14, fontweight='bold', pad=20)

        plt.tight_layout()

        output_path = self.output_dir / "fig7_success_criteria_dashboard.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Graph 7: Success criteria dashboard saved to {output_path}")

    def generate_results_table(self, experiment_metrics: Dict[str, Dict],
                               inference_data: Dict[str, Dict] = None):
        """
        Generate LaTeX/Markdown table for thesis
        """
        print("\n" + "="*80)
        print("THESIS RESULTS TABLE (Markdown Format)")
        print("="*80)

        print("\n| Experiment | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall | F1 | Inference (ms) |")
        print("|------------|---------|--------------|-----------|--------|----|-----------------| ")

        for exp in experiment_metrics.keys():
            metrics = experiment_metrics[exp]
            inf_time = inference_data[exp]['avg_ms'] if inference_data and exp in inference_data else 'N/A'

            print(f"| {exp} | {metrics.get('mAP@0.5', 0):.4f} | "
                  f"{metrics.get('mAP@0.5:0.95', 0):.4f} | "
                  f"{metrics.get('Precision', 0):.4f} | "
                  f"{metrics.get('Recall', 0):.4f} | "
                  f"{metrics.get('F1', 0):.4f} | "
                  f"{inf_time if isinstance(inf_time, str) else f'{inf_time:.2f}'} |")

        # Save to file
        table_file = self.output_dir / "results_table.md"
        with open(table_file, 'w') as f:
            f.write("# LEGO Object Detection - Results Table\n\n")
            f.write("## Overall Performance\n\n")
            f.write("| Experiment | mAP@0.5 | mAP@0.5:0.95 | Precision | Recall | F1 | Inference (ms) |\n")
            f.write("|------------|---------|--------------|-----------|--------|----|-----------------|\n")

            for exp in experiment_metrics.keys():
                metrics = experiment_metrics[exp]
                inf_time = inference_data[exp]['avg_ms'] if inference_data and exp in inference_data else 'N/A'

                f.write(f"| {exp} | {metrics.get('mAP@0.5', 0):.4f} | "
                       f"{metrics.get('mAP@0.5:0.95', 0):.4f} | "
                       f"{metrics.get('Precision', 0):.4f} | "
                       f"{metrics.get('Recall', 0):.4f} | "
                       f"{metrics.get('F1', 0):.4f} | "
                       f"{inf_time if isinstance(inf_time, str) else f'{inf_time:.2f}'} |\n")

        print(f"\n✓ Table saved to: {table_file}")


def main():
    """Main workflow for generating thesis graphs"""
    parser = argparse.ArgumentParser(description="Generate Thesis Results Graphs")
    parser.add_argument("--exp1-results", type=str,
                       help="Path to Experiment 1 results.csv")
    parser.add_argument("--exp1-metrics", type=str,
                       help="Path to Experiment 1 metrics.json")
    parser.add_argument("--exp2-results", type=str,
                       help="Path to Experiment 2 results.csv")
    parser.add_argument("--exp2-metrics", type=str,
                       help="Path to Experiment 2 metrics.json")
    parser.add_argument("--output-dir", type=str,
                       help="Output directory for graphs")
    args = parser.parse_args()

    print("="*80)
    print("LEGO OBJECT DETECTION - THESIS GRAPHS GENERATOR")
    print("="*80)

    generator = ThesisGraphGenerator(args.output_dir)

    # Example usage - you'll need to provide actual paths
    print("\nTo generate graphs, provide paths to your trained models:")
    print("\nExample:")
    print("  python generate_thesis_graphs.py \\")
    print("    --exp1-results training_output/models/experiment_1_*/stage1_synthetic/results.csv \\")
    print("    --exp1-metrics training_output/results/validation_best/metrics.json \\")
    print("    --exp2-results training_output/models/experiment_2_*/stage2_finetuned/results.csv \\")
    print("    --exp2-metrics training_output/results/validation_best/metrics.json")

    # If arguments provided, generate graphs
    if args.exp1_results and args.exp2_results:
        # Load data
        experiment_results = {
            'Experiment 1': Path(args.exp1_results),
            'Experiment 2': Path(args.exp2_results)
        }

        experiment_metrics = {
            'Experiment 1': generator.load_validation_metrics(Path(args.exp1_metrics)),
            'Experiment 2': generator.load_validation_metrics(Path(args.exp2_metrics))
        }

        # Generate all graphs
        generator.plot_training_curves_combined(experiment_results)
        generator.plot_map_progression(experiment_results)
        generator.plot_precision_recall_curves(experiment_results)
        generator.plot_final_metrics_comparison(experiment_metrics)
        generator.plot_per_class_comparison(experiment_metrics)
        generator.plot_success_criteria_dashboard(experiment_metrics)

        # Example inference data (you should provide actual benchmark results)
        inference_data = {
            'Experiment 1': {'avg_ms': 15.3, 'fps': 65.4},
            'Experiment 2': {'avg_ms': 16.1, 'fps': 62.1}
        }
        generator.plot_inference_speed_comparison(inference_data)

        # Generate results table
        generator.generate_results_table(experiment_metrics, inference_data)

        print("\n" + "="*80)
        print("✓ ALL THESIS GRAPHS GENERATED!")
        print("="*80)
        print(f"\nGraphs saved to: {generator.output_dir}")
        print("\nGenerated graphs:")
        print("  1. Training Loss Comparison")
        print("  2. mAP Progression")
        print("  3. Precision/Recall Progression")
        print("  4. Final Metrics Comparison")
        print("  5. Per-Class Performance Comparison")
        print("  6. Inference Speed Comparison")
        print("  7. Success Criteria Dashboard")
        print("  8. Results Table (Markdown)")


if __name__ == "__main__":
    main()
