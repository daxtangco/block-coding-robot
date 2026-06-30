#!/usr/bin/env python3
"""
Model Export Script for LEGO Object Detection
Export trained models to different formats for deployment
"""

import argparse
import sys
from pathlib import Path
import torch
from ultralytics import YOLO

# Windows consoles default to cp1252; force UTF-8 so ✓ glyphs don't crash output.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config import get_model_path, PREPARED_DATA_DIR


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

    def export_tflite(self, int8: bool = False, imgsz: int = 640):
        """Export to TensorFlow Lite (for ESP32-CAM deployment).

        int8=True produces a fully quantized model (smallest size, needed for
        ESP32-CAM). It calibrates on the prepared dataset if data.yaml is found.
        """
        print("\n" + "="*60)
        print(f"Exporting to TensorFlow Lite (int8={int8}, imgsz={imgsz})")
        print("="*60)

        export_args = {"format": "tflite", "int8": int8, "imgsz": imgsz}

        if int8:
            # int8 quantization needs a representative dataset for calibration.
            data_yaml = PREPARED_DATA_DIR / "experiment_2" / "data.yaml"
            if data_yaml.exists():
                export_args["data"] = str(data_yaml)
                print(f"Using calibration data: {data_yaml}")
            else:
                print("⚠ No prepared data.yaml found; int8 calibration will use "
                      "default images. Run prepare_datasets.py for best results.")

        try:
            output_path = self.model.export(**export_args)
            size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            print(f"✓ TFLite model exported to: {output_path} ({size_mb:.2f} MB)")
            print("\nFor ESP32-CAM deployment:")
            print(f"1. Convert to a C header:  xxd -i {Path(output_path).name} > model_data.h")
            print("2. Place model_data.h next to vision_board.ino and #include it")
            print("3. Replace mockInference() with TFLite Micro inference code")
            return output_path

        except Exception as e:
            print(f"✗ TFLite export failed: {e}")
            print("TFLite export requires TensorFlow + ONNX installed")
            print("Install: pip install tensorflow onnx onnx2tf onnxslim")
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

    def export_all_formats(self, int8: bool = False, imgsz: int = 640):
        """Export to all supported formats"""
        print("\n" + "="*70)
        print("EXPORTING TO ALL FORMATS")
        print("="*70)

        formats = {
            "ONNX": self.export_onnx,
            "TFLite": lambda: self.export_tflite(int8=int8, imgsz=imgsz),
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
    parser.add_argument("--model", type=str, default=None,
                        help="Path to trained model weights (.pt file). "
                             "If omitted, auto-discovers from models/ or training_output/.")
    parser.add_argument("--format", type=str, choices=["onnx", "tflite", "torchscript", "all"],
                        default="all", help="Export format (default: all)")
    parser.add_argument("--int8", action="store_true",
                        help="Use int8 quantization for TFLite (smallest, for ESP32-CAM)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Export input image size (default: 640; use smaller e.g. 320/160 for ESP32-CAM)")
    args = parser.parse_args()

    print("="*70)
    print("LEGO OBJECT DETECTION - MODEL EXPORT")
    print("="*70)

    # Resolve model path (explicit flag wins, else auto-discover)
    model_path = args.model
    if model_path is None:
        found = get_model_path()
        if found is None:
            print("\n✗ No trained model found.")
            print("  Place your trained best.pt at: models/lego_detector.pt")
            sys.exit(1)
        model_path = str(found)
        print(f"Auto-discovered model: {model_path}")

    # Initialize exporter
    exporter = ModelExporter(model_path)

    # Display model info
    exporter.get_model_info()

    # Export
    if args.format == "all":
        exporter.export_all_formats(int8=args.int8, imgsz=args.imgsz)
    elif args.format == "onnx":
        exporter.export_onnx()
    elif args.format == "tflite":
        exporter.export_tflite(int8=args.int8, imgsz=args.imgsz)
    elif args.format == "torchscript":
        exporter.export_torchscript()

    print("\n" + "="*70)
    print("EXPORT COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
