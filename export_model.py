#!/usr/bin/env python3
"""
Model Export Script for LEGO Object Detection
Export trained models to different formats for deployment
"""

import argparse
from pathlib import Path
import torch
from ultralytics import YOLO


class ModelExporter:
    """Export YOLOv8 models to various formats"""

    def __init__(self, model_path: str):
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        print(f"Loading model: {self.model_path}")
        self.model = YOLO(str(self.model_path))

        self.output_dir = self.model_path.parent / "exports"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_onnx(self):
        """Export to ONNX format (for deployment on various platforms)"""
        print("\n" + "="*60)
        print("Exporting to ONNX format")
        print("="*60)

        output_path = self.model.export(
            format="onnx",
            simplify=True,
            opset=12
        )

        print(f"✓ ONNX model exported to: {output_path}")
        return output_path

    def export_tflite(self):
        """Export to TensorFlow Lite (for ESP32-CAM deployment)"""
        print("\n" + "="*60)
        print("Exporting to TensorFlow Lite format")
        print("="*60)

        try:
            output_path = self.model.export(
                format="tflite",
                int8=False  # Use float16 for better accuracy
            )

            print(f"✓ TFLite model exported to: {output_path}")
            print("\nFor ESP32-CAM deployment:")
            print("1. Convert to TFLite Micro format")
            print("2. Quantize to INT8 for smaller size")
            print("3. Include in ESP32 firmware")

            return output_path

        except Exception as e:
            print(f"✗ TFLite export failed: {e}")
            print("TFLite export requires TensorFlow installed")
            print("Install: pip install tensorflow")
            return None

    def export_torchscript(self):
        """Export to TorchScript format (for C++ deployment)"""
        print("\n" + "="*60)
        print("Exporting to TorchScript format")
        print("="*60)

        output_path = self.model.export(format="torchscript")

        print(f"✓ TorchScript model exported to: {output_path}")
        return output_path

    def export_openvino(self):
        """Export to OpenVINO format (for Intel hardware optimization)"""
        print("\n" + "="*60)
        print("Exporting to OpenVINO format")
        print("="*60)

        try:
            output_path = self.model.export(format="openvino")
            print(f"✓ OpenVINO model exported to: {output_path}")
            return output_path
        except Exception as e:
            print(f"✗ OpenVINO export failed: {e}")
            return None

    def export_all_formats(self):
        """Export to all supported formats"""
        print("\n" + "="*70)
        print("EXPORTING TO ALL FORMATS")
        print("="*70)

        formats = {
            "ONNX": self.export_onnx,
            "TFLite": self.export_tflite,
            "TorchScript": self.export_torchscript,
        }

        results = {}
        for format_name, export_func in formats.items():
            try:
                results[format_name] = export_func()
            except Exception as e:
                print(f"\n✗ {format_name} export failed: {e}")
                results[format_name] = None

        print("\n" + "="*70)
        print("EXPORT SUMMARY")
        print("="*70)

        for format_name, path in results.items():
            if path:
                print(f"✓ {format_name:12s}: {path}")
            else:
                print(f"✗ {format_name:12s}: Failed")

        print(f"\nAll exports saved to: {self.output_dir}")

        return results

    def get_model_info(self):
        """Display model information"""
        print("\n" + "="*60)
        print("MODEL INFORMATION")
        print("="*60)

        model_info = self.model.info()

        print(f"Model file: {self.model_path}")
        print(f"Model size: {self.model_path.stat().st_size / (1024*1024):.2f} MB")

        # Get input/output info
        try:
            print(f"\nModel architecture: YOLOv8")
            print(f"Input shape: (batch, 3, 640, 640)")
            print(f"Output: Bounding boxes with class predictions")
        except Exception:
            pass

        return model_info


def main():
    """Main export workflow"""
    parser = argparse.ArgumentParser(description="Export LEGO Object Detection Model")
    parser.add_argument("--model", type=str, required=True,
                        help="Path to trained model weights (.pt file)")
    parser.add_argument("--format", type=str, choices=["onnx", "tflite", "torchscript", "all"],
                        default="all", help="Export format (default: all)")
    args = parser.parse_args()

    print("="*70)
    print("LEGO OBJECT DETECTION - MODEL EXPORT")
    print("="*70)

    # Initialize exporter
    exporter = ModelExporter(args.model)

    # Display model info
    exporter.get_model_info()

    # Export
    if args.format == "all":
        exporter.export_all_formats()
    elif args.format == "onnx":
        exporter.export_onnx()
    elif args.format == "tflite":
        exporter.export_tflite()
    elif args.format == "torchscript":
        exporter.export_torchscript()

    print("\n" + "="*70)
    print("EXPORT COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
