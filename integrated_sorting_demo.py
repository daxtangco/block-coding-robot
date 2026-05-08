#!/usr/bin/env python3
"""
Integrated LEGO Detection + Sorting Demo
Combines YOLOv8 detection with robotic arm sorting logic
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple
from ultralytics import YOLO

from sorting_logic import LEGOSorter, Detection


class IntegratedSortingSystem:
    """Complete LEGO detection and sorting system"""

    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        """
        Initialize detection and sorting system.

        Args:
            model_path: Path to trained YOLOv8 model (.pt file)
            confidence_threshold: Minimum confidence for detection (0.0-1.0)
        """
        # Load trained YOLOv8 model
        print(f"Loading model: {model_path}")
        self.model = YOLO(model_path)

        # Initialize sorter
        self.sorter = LEGOSorter()

        # Set confidence threshold
        self.conf_threshold = confidence_threshold

        print(f"✓ System initialized (conf >= {confidence_threshold})")

    def detect_legos(self, image_path: str) -> List[Detection]:
        """
        Detect LEGO bricks in image.

        Args:
            image_path: Path to input image

        Returns:
            List of Detection objects
        """
        # Run YOLOv8 inference
        results = self.model(image_path, conf=self.conf_threshold, verbose=False)

        # Convert YOLOv8 results to Detection objects
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                # Get class name
                class_name = result.names[class_id]

                detection = Detection(
                    class_name=class_name,
                    confidence=confidence,
                    bbox=tuple(map(int, bbox))
                )
                detections.append(detection)

        return detections

    def process_image(self, image_path: str) -> dict:
        """
        Complete processing: detect + generate sorting instructions.

        Args:
            image_path: Path to input image

        Returns:
            Dictionary with detections and sorting sequence
        """
        print(f"\nProcessing: {image_path}")

        # Detect LEGO bricks
        detections = self.detect_legos(image_path)
        print(f"  Found {len(detections)} LEGO bricks")

        if not detections:
            return {
                "image_path": image_path,
                "detections": [],
                "sorting_sequence": [],
                "bin_statistics": {}
            }

        # Generate sorting sequence
        sorting_sequence = self.sorter.generate_sorting_sequence(detections)

        # Get bin statistics
        bin_stats = self.sorter.get_bin_statistics(detections)

        return {
            "image_path": image_path,
            "detections": detections,
            "sorting_sequence": sorting_sequence,
            "bin_statistics": bin_stats
        }

    def visualize_detections(self, image_path: str, output_path: str = None) -> str:
        """
        Create annotated image with detections and sorting info.

        Args:
            image_path: Path to input image
            output_path: Path to save annotated image (optional)

        Returns:
            Path to saved image
        """
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Cannot read image: {image_path}")

        # Detect bricks
        detections = self.detect_legos(image_path)

        # Draw bounding boxes and labels
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            conf = detection.confidence
            class_name = detection.class_name

            # Get target bin
            bin_name, _ = self.sorter.get_target_bin(class_name)

            # Draw bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Draw label with class, confidence, and target bin
            label = f"{class_name} {conf:.2f} -> {bin_name}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(image, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(image, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

            # Draw center point (pickup position)
            center = detection.center
            cv2.circle(image, center, 5, (0, 0, 255), -1)

        # Add summary text
        summary = f"Total: {len(detections)} bricks detected"
        cv2.putText(image, summary, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Save
        if output_path is None:
            output_path = str(Path(image_path).stem) + "_sorted.jpg"

        cv2.imwrite(output_path, image)
        print(f"  Saved annotated image: {output_path}")

        return output_path

    def print_sorting_instructions(self, result: dict):
        """
        Print detailed sorting instructions for robot arm.

        Args:
            result: Result dictionary from process_image()
        """
        print("\n" + "="*70)
        print("ROBOTIC ARM SORTING INSTRUCTIONS")
        print("="*70)

        sequence = result["sorting_sequence"]

        if not sequence:
            print("No LEGO bricks detected.")
            return

        for i, instruction in enumerate(sequence, 1):
            print(f"\n[Step {i}]")
            print(f"  1. IDENTIFY: {instruction['brick_class']} "
                  f"(confidence: {instruction['confidence']:.1%})")
            print(f"  2. MOVE TO: Pickup position {instruction['pickup_position']}")
            print(f"  3. PICK UP: Close gripper")
            print(f"  4. MOVE TO: {instruction['target_bin']} "
                  f"at {instruction['dropoff_position']}")
            print(f"  5. DROP OFF: Open gripper")
            print(f"  6. RETURN: Move to home position")

        # Print summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total operations: {len(sequence)}")
        print(f"\nBin distribution:")
        for bin_name, count in result["bin_statistics"].items():
            print(f"  {bin_name}: {count} bricks")

        # Calculate estimated time (assuming 10 seconds per operation)
        estimated_time = len(sequence) * 10
        print(f"\nEstimated completion time: {estimated_time} seconds "
              f"({estimated_time/60:.1f} minutes)")


def demo_workflow():
    """
    Demonstration workflow for thesis
    Shows complete detection → sorting pipeline
    """
    print("="*70)
    print("LEGO DETECTION + SORTING SYSTEM DEMO")
    print("="*70)

    # Initialize system with trained model
    model_path = "training_output/models/experiment_2_TIMESTAMP/stage2_finetuned/weights/best.pt"

    # Check if model exists
    if not Path(model_path).exists():
        print(f"\n⚠ Model not found: {model_path}")
        print("Please train the model first or update the path.")
        return

    system = IntegratedSortingSystem(model_path, confidence_threshold=0.5)

    # Example: Process test image
    test_image = "datasets/images/00000.jpg"

    if not Path(test_image).exists():
        print(f"\n⚠ Test image not found: {test_image}")
        print("Please provide a valid image path.")
        return

    # Run detection and sorting
    result = system.process_image(test_image)

    # Generate visual output
    system.visualize_detections(test_image, "demo_output.jpg")

    # Print instructions for robot
    system.print_sorting_instructions(result)

    print("\n" + "="*70)
    print("✓ DEMO COMPLETE")
    print("="*70)
    print(f"Check demo_output.jpg for visual results")


def generate_arduino_code(result: dict) -> str:
    """
    Generate Arduino-compatible sorting commands.

    Args:
        result: Result dictionary from process_image()

    Returns:
        Arduino C++ code as string
    """
    code = []
    code.append("// Auto-generated LEGO sorting sequence")
    code.append("// Generated from detection results\n")

    for i, instruction in enumerate(result["sorting_sequence"]):
        step = i + 1
        brick = instruction["brick_class"]
        pickup = instruction["pickup_position"]
        dropoff = instruction["dropoff_position"]

        code.append(f"// Step {step}: Sort {brick}")
        code.append(f"moveToPosition({pickup[0]}, {pickup[1]}, 100);  // Pickup")
        code.append("closeClaw();")
        code.append("delay(500);")
        code.append(f"moveToPosition({dropoff[0]}, {dropoff[1]}, {dropoff[2]});  // Dropoff")
        code.append("openClaw();")
        code.append("delay(500);")
        code.append("moveToHome();\n")

    return "\n".join(code)


if __name__ == "__main__":
    # Run demo
    demo_workflow()

    # Example: Generate Arduino code
    # result = system.process_image("test.jpg")
    # arduino_code = generate_arduino_code(result)
    # print(arduino_code)
