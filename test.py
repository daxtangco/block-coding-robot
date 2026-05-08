#!/usr/bin/env python3
"""
Testing/Inference Script for LEGO Object Detection
Test trained models on individual images or batches
"""

import argparse
from pathlib import Path
import cv2
import torch
from ultralytics import YOLO
import matplotlib.pyplot as plt
from config import TARGET_CLASSES, RESULTS_DIR


class LEGODetector:
    """LEGO Object Detection Inference"""

    def __init__(self, model_path: str):
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        print(f"Loading model: {self.model_path}")
        self.model = YOLO(str(self.model_path))

        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Output directory
        self.output_dir = RESULTS_DIR / f"predictions_{self.model_path.stem}"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def predict_image(self, image_path: str, conf_threshold: float = 0.25,
                     save_result: bool = True, show_labels: bool = True):
        """Run detection on a single image"""
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        print(f"\nProcessing: {image_path.name}")

        # Run inference
        results = self.model(
            str(image_path),
            conf=conf_threshold,
            device=self.device,
            verbose=False
        )

        result = results[0]

        # Get detections
        boxes = result.boxes
        n_detections = len(boxes)

        print(f"  Detections: {n_detections}")

        # Print detection details
        if n_detections > 0 and show_labels:
            for i, box in enumerate(boxes):
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = TARGET_CLASSES[class_id] if class_id < len(TARGET_CLASSES) else f"Class_{class_id}"
                print(f"    [{i+1}] {class_name}: {confidence:.2f}")

        # Save annotated image
        if save_result:
            output_path = self.output_dir / f"pred_{image_path.stem}.jpg"
            annotated = result.plot()
            cv2.imwrite(str(output_path), annotated)
            print(f"  Saved to: {output_path}")

        return result

    def predict_batch(self, image_dir: str, conf_threshold: float = 0.25,
                     save_results: bool = True):
        """Run detection on all images in a directory"""
        image_dir = Path(image_dir)

        if not image_dir.exists():
            raise FileNotFoundError(f"Directory not found: {image_dir}")

        # Get all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(image_dir.glob(f"*{ext}"))
            image_files.extend(image_dir.glob(f"*{ext.upper()}"))

        if not image_files:
            print(f"No images found in {image_dir}")
            return

        print(f"\nProcessing {len(image_files)} images from {image_dir}")

        # Create batch output directory
        batch_output_dir = self.output_dir / f"batch_{image_dir.name}"
        batch_output_dir.mkdir(parents=True, exist_ok=True)

        # Process each image
        all_results = []
        detection_stats = {class_name: 0 for class_name in TARGET_CLASSES}

        for img_path in image_files:
            results = self.model(
                str(img_path),
                conf=conf_threshold,
                device=self.device,
                verbose=False
            )

            result = results[0]
            all_results.append(result)

            # Count detections by class
            for box in result.boxes:
                class_id = int(box.cls[0])
                if class_id < len(TARGET_CLASSES):
                    detection_stats[TARGET_CLASSES[class_id]] += 1

            # Save annotated image
            if save_results:
                output_path = batch_output_dir / f"pred_{img_path.name}"
                annotated = result.plot()
                cv2.imwrite(str(output_path), annotated)

        # Print statistics
        print("\n" + "="*60)
        print("Batch Processing Statistics")
        print("="*60)
        print(f"Total images processed: {len(image_files)}")
        print(f"Total detections: {sum(detection_stats.values())}")
        print(f"\nDetections by class:")
        for class_name, count in sorted(detection_stats.items()):
            if count > 0:
                print(f"  {class_name}: {count}")

        if save_results:
            print(f"\n✓ Results saved to: {batch_output_dir}")

        return all_results

    def benchmark_speed(self, image_path: str, n_runs: int = 100):
        """Benchmark inference speed on a single image"""
        import time

        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        print(f"\n" + "="*60)
        print(f"Benchmarking inference speed")
        print(f"Image: {image_path.name}")
        print(f"Runs: {n_runs}")
        print("="*60)

        # Warm-up
        print("\nWarming up...")
        for _ in range(10):
            _ = self.model(str(image_path), verbose=False)

        # Benchmark
        print(f"Running {n_runs} iterations...")
        times = []

        for _ in range(n_runs):
            start = time.time()
            _ = self.model(str(image_path), verbose=False)
            times.append((time.time() - start) * 1000)  # Convert to ms

        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        fps = 1000 / avg_time

        print(f"\n" + "="*60)
        print("Benchmark Results")
        print("="*60)
        print(f"Average inference time: {avg_time:.2f} ms")
        print(f"Min inference time:     {min_time:.2f} ms")
        print(f"Max inference time:     {max_time:.2f} ms")
        print(f"FPS:                    {fps:.2f}")
        print(f"Device:                 {self.device}")

        # Check real-time capability
        if fps >= 10:
            print(f"\n✓ Model is suitable for real-time robotics (>= 10 FPS)")
        else:
            print(f"\n✗ Model may be too slow for real-time use")
            print(f"  Consider optimization or using a lighter model variant")

        return {"avg_ms": avg_time, "fps": fps, "min_ms": min_time, "max_ms": max_time}

    def test_with_visualization(self, image_path: str, conf_threshold: float = 0.25):
        """Test and display results with matplotlib"""
        result = self.predict_image(image_path, conf_threshold, save_result=False)

        # Get annotated image
        annotated = result.plot()
        annotated = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

        # Display
        plt.figure(figsize=(12, 8))
        plt.imshow(annotated)
        plt.axis('off')
        plt.title(f'LEGO Detection Results - {Path(image_path).name}', fontsize=14, fontweight='bold')
        plt.tight_layout()

        output_path = self.output_dir / f"viz_{Path(image_path).stem}.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  Visualization saved to: {output_path}")
        plt.close()


def main():
    """Main testing workflow"""
    parser = argparse.ArgumentParser(description="Test LEGO Object Detection Model")
    parser.add_argument("--model", type=str, required=True,
                        help="Path to trained model weights (.pt file)")
    parser.add_argument("--image", type=str,
                        help="Path to single image for inference")
    parser.add_argument("--batch", type=str,
                        help="Path to directory of images for batch inference")
    parser.add_argument("--conf", type=float, default=0.25,
                        help="Confidence threshold (default: 0.25)")
    parser.add_argument("--benchmark", action="store_true",
                        help="Run inference speed benchmark")
    parser.add_argument("--visualize", action="store_true",
                        help="Create visualization with matplotlib")
    args = parser.parse_args()

    if not args.image and not args.batch:
        parser.error("Either --image or --batch must be specified")

    print("="*70)
    print("LEGO OBJECT DETECTION - TESTING/INFERENCE")
    print("="*70)

    # Initialize detector
    detector = LEGODetector(args.model)

    # Single image inference
    if args.image:
        if args.visualize:
            detector.test_with_visualization(args.image, args.conf)
        else:
            detector.predict_image(args.image, args.conf)

        if args.benchmark:
            detector.benchmark_speed(args.image)

    # Batch inference
    if args.batch:
        detector.predict_batch(args.batch, args.conf)

    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {detector.output_dir}")


if __name__ == "__main__":
    main()
