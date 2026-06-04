# LEGO Sorting System Guide

Complete guide for integrating LEGO detection with robotic arm sorting.

---

## 🎯 System Overview

The sorting system has **two components**:

1. **Detection**: YOLOv8 model detects LEGO bricks
2. **Sorting Logic**: Maps bricks to bins using fixed positions

```
┌─────────────────────────────────────────────────────────┐
│                   COMPLETE WORKFLOW                     │
└─────────────────────────────────────────────────────────┘

  Camera Image
      ↓
  [YOLOv8 Detection]
      ↓
  LEGO Bricks Detected
  (class, bbox, confidence)
      ↓
  [Sorting Logic]
      ↓
  Target Bin Assignment
  (pickup pos → dropoff pos)
      ↓
  [Robotic Arm Execution]
      ↓
  Bricks Sorted!
```

---

## 📁 New Files Created

**Sorting System (2 files):**
1. `sorting_logic.py` - Bin mapping and sorting rules
2. `integrated_sorting_demo.py` - Complete detection + sorting demo

---

## 🗂️ Bin Configuration

### Default Setup (3 Bins)

```python
BIN_POSITIONS = {
    "small_bin": (150, 200, 50),    # For 1x1, 1x2
    "medium_bin": (250, 200, 50),   # For 2x2, 2x4
    "large_bin": (350, 200, 50),    # For 2x6, 2x8, 2x10, 2x12
}

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
```

**Positions are in millimeters (x, y, z) relative to arm base.**

---

## 🔧 Calibration Process

### Step 1: Measure Bin Positions

1. Place bins in workspace
2. Move robot arm to center of each bin
3. Record coordinates from arm controller
4. Update `BIN_POSITIONS` in `sorting_logic.py`

### Step 2: Test Positioning

```python
from sorting_logic import LEGOSorter

sorter = LEGOSorter()

# Test each bin position
for bin_name, position in sorter.bin_positions.items():
    print(f"Move arm to {bin_name}: {position}")
    # Verify arm reaches correct bin
```

### Step 3: Adjust if Needed

```python
# If bins are in different positions, override:
custom_bins = {
    "small_bin": (180, 220, 45),   # Your measured position
    "medium_bin": (280, 220, 45),
    "large_bin": (380, 220, 45),
}

sorter = LEGOSorter(bin_positions=custom_bins)
```

---

## 🚀 Usage Examples

### Example 1: Basic Detection + Sorting

```python
from integrated_sorting_demo import IntegratedSortingSystem

# Initialize system
system = IntegratedSortingSystem(
    model_path="path/to/best.pt",
    confidence_threshold=0.5
)

# Process image
result = system.process_image("workspace_image.jpg")

# Get sorting sequence
for instruction in result["sorting_sequence"]:
    print(f"Pick {instruction['brick_class']} from {instruction['pickup_position']}")
    print(f"Drop in {instruction['target_bin']} at {instruction['dropoff_position']}")
```

---

### Example 2: Generate Sorting Instructions

```python
# Process workspace image
result = system.process_image("workspace.jpg")

# Print detailed instructions
system.print_sorting_instructions(result)
```

**Output:**
```
==================================================================
ROBOTIC ARM SORTING INSTRUCTIONS
==================================================================

[Step 1]
  1. IDENTIFY: 2x4 (confidence: 92.5%)
  2. MOVE TO: Pickup position (250, 175)
  3. PICK UP: Close gripper
  4. MOVE TO: medium_bin at (250, 200, 50)
  5. DROP OFF: Open gripper
  6. RETURN: Move to home position

[Step 2]
  1. IDENTIFY: 1x1 (confidence: 89.3%)
  ...
```

---

### Example 3: Create Annotated Image

```python
# Visualize detections with target bins
system.visualize_detections(
    image_path="workspace.jpg",
    output_path="annotated_result.jpg"
)
```

**Annotations include:**
- Bounding boxes around LEGO bricks
- Class name + confidence
- Target bin assignment
- Pickup position (red dot)

---

### Example 4: Custom Sorting Rules

```python
from sorting_logic import LEGOSorter

# Custom rules: sort by size differently
custom_rules = {
    "1x1": "bin_A",
    "1x2": "bin_A",
    "2x2": "bin_B",
    "2x4": "bin_B",
    "2x6": "bin_C",
    "2x8": "bin_C",
    "2x10": "bin_D",  # Extra bin for very large
    "2x12": "bin_D",
}

custom_bins = {
    "bin_A": (100, 200, 50),
    "bin_B": (200, 200, 50),
    "bin_C": (300, 200, 50),
    "bin_D": (400, 200, 50),
}

sorter = LEGOSorter(
    bin_positions=custom_bins,
    sorting_rules=custom_rules
)
```

---

## 🤖 Integration with Robotic Arm

### Arduino Code Generation

```python
from integrated_sorting_demo import generate_arduino_code

# Process image
result = system.process_image("workspace.jpg")

# Generate Arduino code
arduino_code = generate_arduino_code(result)

# Save to file
with open("sorting_sequence.ino", "w") as f:
    f.write(arduino_code)
```

**Generated code:**
```cpp
// Auto-generated LEGO sorting sequence

// Step 1: Sort 2x4
moveToPosition(250, 175, 100);  // Pickup
closeClaw();
delay(500);
moveToPosition(250, 200, 50);  // Dropoff
openClaw();
delay(500);
moveToHome();

// Step 2: Sort 1x1
moveToPosition(120, 90, 100);  // Pickup
...
```

---

### Block-Based Integration

In your Blockly IDE, use these blocks:

```
forever
  if camera sees any LEGO
    result = detect_and_sort()  // Returns sorting instructions
    for each brick in result
      move arm to brick.pickup_position
      close claw
      wait 500 ms
      move arm to brick.dropoff_position
      open claw
      wait 500 ms
      move arm to HOME
```

---

## 📊 Sorting Statistics

```python
# Get bin statistics
result = system.process_image("workspace.jpg")

stats = result["bin_statistics"]
print(f"small_bin: {stats['small_bin']} bricks")
print(f"medium_bin: {stats['medium_bin']} bricks")
print(f"large_bin: {stats['large_bin']} bricks")
```

**Output:**
```
small_bin: 5 bricks
medium_bin: 8 bricks
large_bin: 3 bricks
Total: 16 bricks to sort
```

---

## ⚙️ Configuration Options

### Confidence Threshold

```python
# High precision (fewer false positives)
system = IntegratedSortingSystem(model_path, confidence_threshold=0.7)

# Balanced (default)
system = IntegratedSortingSystem(model_path, confidence_threshold=0.5)

# High recall (detect more bricks)
system = IntegratedSortingSystem(model_path, confidence_threshold=0.3)
```

**Recommendation:** Use 0.5 for thesis demo (good balance)

---

### Sorting Priority

By default, bricks are sorted by **confidence** (most confident first).

**Custom priority:**
```python
# Sort by size (smallest first)
size_priority = ["1x1", "1x2", "2x2", "2x4", "2x6", "2x8", "2x10", "2x12"]
detections.sort(key=lambda d: size_priority.index(d.class_name))

# Sort by position (left to right)
detections.sort(key=lambda d: d.center[0])
```

---

## 🎓 Thesis Demonstration

### Complete Workflow

```python
from integrated_sorting_demo import IntegratedSortingSystem

# 1. Initialize system
system = IntegratedSortingSystem("path/to/best.pt")

# 2. Capture workspace image
workspace_image = capture_from_camera()  # ESP32-CAM

# 3. Detect and sort
result = system.process_image(workspace_image)

# 4. Execute on robot
for instruction in result["sorting_sequence"]:
    robot.move_to(instruction["pickup_position"])
    robot.close_gripper()
    robot.move_to(instruction["dropoff_position"])
    robot.open_gripper()
    robot.move_to_home()

# 5. Report results
print(f"✓ Sorted {len(result['detections'])} LEGO bricks")
print(f"  Accuracy: {calculate_accuracy()}%")
```

---

## 📈 Success Metrics

Track these for your thesis:

```python
# Sorting success rate
successful_sorts = 0
total_attempts = 0

for brick in detected_bricks:
    if sort_brick(brick) == SUCCESS:
        successful_sorts += 1
    total_attempts += 1

success_rate = successful_sorts / total_attempts * 100
print(f"Sorting success rate: {success_rate:.1f}%")
```

**Target (from PRD):** ≥ 90% sorting success rate

---

## 🔍 Troubleshooting

### Issue: Arm misses pickup position

**Cause:** Camera-to-arm coordinate transformation error

**Solution:**
```python
# Add camera calibration
def camera_to_arm_coordinates(image_x, image_y):
    # Apply calibration matrix
    arm_x = image_x * scale_x + offset_x
    arm_y = image_y * scale_y + offset_y
    return arm_x, arm_y
```

---

### Issue: Wrong bin selected

**Cause:** Detection confidence too low or wrong class

**Solution:**
- Increase confidence threshold
- Re-train model with more data
- Verify sorting rules in `sorting_logic.py`

---

### Issue: Bins not reachable

**Cause:** Bin positions outside arm's reach

**Solution:**
1. Measure arm's maximum reach
2. Place bins within reach
3. Update `BIN_POSITIONS` with measured coordinates

---

## 📝 Thesis Documentation

### Figure: System Architecture

```
┌─────────────┐
│  ESP32-CAM  │ (Capture workspace)
└──────┬──────┘
       │ Image
       ↓
┌─────────────┐
│  YOLOv8     │ (Detect LEGO bricks)
│  Detection  │
└──────┬──────┘
       │ Detections (class, bbox, conf)
       ↓
┌─────────────┐
│  Sorting    │ (Map to bins)
│  Logic      │
└──────┬──────┘
       │ Instructions (pickup → dropoff)
       ↓
┌─────────────┐
│  Robotic    │ (Execute movements)
│  Arm        │
└─────────────┘
```

### Table: Sorting Rules

| LEGO Class | Target Bin | Bin Position (x, y, z) |
|------------|------------|------------------------|
| 1x1 | small_bin | (150, 200, 50) |
| 1x2 | small_bin | (150, 200, 50) |
| 2x2 | medium_bin | (250, 200, 50) |
| 2x4 | medium_bin | (250, 200, 50) |
| 2x6 | large_bin | (350, 200, 50) |
| 2x8 | large_bin | (350, 200, 50) |
| 2x10 | large_bin | (350, 200, 50) |
| 2x12 | large_bin | (350, 200, 50) |

---

## 🎯 Summary

**What You Have:**
- ✅ LEGO brick detection (YOLOv8)
- ✅ Sorting logic (fixed bin positions)
- ✅ Integration demo
- ✅ Arduino code generation
- ✅ Visual annotations

**What You Need to Do:**
1. Train detection model (or use pre-trained)
2. Calibrate bin positions for your setup
3. Run `integrated_sorting_demo.py` to test
4. Integrate with your robotic arm controller
5. Measure sorting success rate for thesis

**No additional training needed!** Just configure bin positions.

---

## 🔗 Related Files

- `sorting_logic.py` - Core sorting rules
- `integrated_sorting_demo.py` - Complete demo
- `train.py` - Train detection model
- `test.py` - Test detection accuracy

---

**Ready to sort LEGO bricks automatically! 🤖📦**
