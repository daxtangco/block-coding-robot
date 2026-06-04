#!/usr/bin/env python3
"""
LEGO Sorting Logic for Robotic Arm
Maps detected LEGO bricks to sorting bins using fixed positions
"""

from typing import Dict, Tuple, List
from dataclasses import dataclass

# LEGO brick classes (from training model)
LEGO_CLASSES = ["1x1", "1x2", "2x2", "2x4", "2x6", "2x8", "2x10", "2x12"]

# Bin positions (x, y, z) in millimeters relative to arm base
# These are fixed positions that you calibrate once
BIN_POSITIONS = {
    "small_bin": (150, 200, 50),    # For 1x1, 1x2
    "medium_bin": (250, 200, 50),   # For 2x2, 2x4
    "large_bin": (350, 200, 50),    # For 2x6, 2x8, 2x10, 2x12
}

# Sorting rules: map each LEGO class to a bin
SORTING_RULES = {
    "1x1": "small_bin",
    "1x2": "small_bin",
    "2x2": "medium_bin",
    "2x4": "medium_bin",
    "2x6": "large_bin",
    "2x8": "large_bin",
    "2x10": "large_bin",
    "2x12": "large_bin",
}


@dataclass
class Detection:
    """LEGO brick detection result"""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)

    @property
    def center(self) -> Tuple[int, int]:
        """Get center point of bounding box"""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)


class LEGOSorter:
    """LEGO sorting logic for robotic arm"""

    def __init__(self,
                 bin_positions: Dict[str, Tuple[int, int, int]] = BIN_POSITIONS,
                 sorting_rules: Dict[str, str] = SORTING_RULES):
        """
        Initialize sorter with bin positions and rules.

        Args:
            bin_positions: Dictionary mapping bin names to (x, y, z) coordinates
            sorting_rules: Dictionary mapping LEGO class names to bin names
        """
        self.bin_positions = bin_positions
        self.sorting_rules = sorting_rules

    def get_target_bin(self, lego_class: str) -> Tuple[str, Tuple[int, int, int]]:
        """
        Get target bin name and position for a LEGO brick class.

        Args:
            lego_class: LEGO brick class name (e.g., "2x4")

        Returns:
            Tuple of (bin_name, bin_position)

        Example:
            >>> sorter = LEGOSorter()
            >>> bin_name, position = sorter.get_target_bin("2x4")
            >>> print(bin_name, position)
            medium_bin (250, 200, 50)
        """
        if lego_class not in self.sorting_rules:
            raise ValueError(f"Unknown LEGO class: {lego_class}")

        bin_name = self.sorting_rules[lego_class]
        bin_position = self.bin_positions[bin_name]

        return bin_name, bin_position

    def sort_detection(self, detection: Detection) -> Dict:
        """
        Get sorting instructions for a detected LEGO brick.

        Args:
            detection: Detection object from YOLOv8 model

        Returns:
            Dictionary with sorting instructions

        Example:
            >>> detection = Detection("2x4", 0.92, (100, 150, 200, 250))
            >>> instructions = sorter.sort_detection(detection)
            >>> print(instructions)
            {
                'brick_class': '2x4',
                'confidence': 0.92,
                'pickup_position': (150, 200),  # center of bbox
                'target_bin': 'medium_bin',
                'dropoff_position': (250, 200, 50)
            }
        """
        bin_name, bin_position = self.get_target_bin(detection.class_name)

        return {
            "brick_class": detection.class_name,
            "confidence": detection.confidence,
            "pickup_position": detection.center,
            "target_bin": bin_name,
            "dropoff_position": bin_position
        }

    def generate_sorting_sequence(self, detections: List[Detection]) -> List[Dict]:
        """
        Generate complete sorting sequence for multiple detections.

        Args:
            detections: List of Detection objects

        Returns:
            List of sorting instructions ordered by priority

        Example:
            >>> detections = [
            ...     Detection("1x1", 0.95, (50, 50, 100, 100)),
            ...     Detection("2x4", 0.92, (200, 100, 300, 200)),
            ... ]
            >>> sequence = sorter.generate_sorting_sequence(detections)
        """
        # Sort by confidence (highest first) for reliability
        sorted_detections = sorted(detections, key=lambda d: d.confidence, reverse=True)

        sequence = []
        for detection in sorted_detections:
            instructions = self.sort_detection(detection)
            sequence.append(instructions)

        return sequence

    def get_bin_statistics(self, detections: List[Detection]) -> Dict[str, int]:
        """
        Get count of bricks going to each bin.

        Args:
            detections: List of Detection objects

        Returns:
            Dictionary mapping bin names to counts
        """
        stats = {bin_name: 0 for bin_name in self.bin_positions.keys()}

        for detection in detections:
            bin_name, _ = self.get_target_bin(detection.class_name)
            stats[bin_name] += 1

        return stats


def example_usage():
    """Example usage for thesis demonstration"""

    # Initialize sorter
    sorter = LEGOSorter()

    # Example detections from YOLOv8 model
    detections = [
        Detection("1x1", 0.95, (50, 50, 100, 100)),
        Detection("2x4", 0.92, (200, 100, 300, 200)),
        Detection("2x8", 0.89, (350, 150, 500, 250)),
        Detection("1x2", 0.87, (100, 300, 150, 350)),
    ]

    # Generate sorting sequence
    print("="*60)
    print("LEGO SORTING SEQUENCE")
    print("="*60)

    sequence = sorter.generate_sorting_sequence(detections)

    for i, instruction in enumerate(sequence, 1):
        print(f"\nStep {i}:")
        print(f"  Brick: {instruction['brick_class']} (confidence: {instruction['confidence']:.2f})")
        print(f"  Pick from: {instruction['pickup_position']}")
        print(f"  Drop in: {instruction['target_bin']} at {instruction['dropoff_position']}")

    # Show bin statistics
    print("\n" + "="*60)
    print("SORTING STATISTICS")
    print("="*60)

    stats = sorter.get_bin_statistics(detections)
    for bin_name, count in stats.items():
        print(f"  {bin_name}: {count} bricks")

    print(f"\nTotal bricks to sort: {len(detections)}")


if __name__ == "__main__":
    example_usage()
