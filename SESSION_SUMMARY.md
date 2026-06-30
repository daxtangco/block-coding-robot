# Block-Coding Robot — Session Summary

## Project Overview
A Blockly IDE (FastAPI backend + vanilla JS frontend) that compiles and flashes AP-mode WiFi firmware to an ESP32 robot arm with a PCA9685 servo driver. Students use block coding to program arm poses and sequences.

**Run the server:**
```
cd "C:\Users\DaxAxisTangco\Documents\acads\thesis\block-coding-robot"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
Open `http://127.0.0.1:8000` in Chrome/Edge.

---

## Hardware
- ESP32 dev board (CP210x USB-UART, COM3)
- PCA9685 16-channel PWM servo driver (I2C: SDA=21, SCL=22)
- 5 servos: Base, Shoulder, Elbow, Wrist, Gripper
- Power: 5V ≥3A dedicated supply for servos; common ground between adapter, PCA9685, and ESP32 GND
- arduino-cli 1.5.0 at `C:\Users\DaxAxisTangco\Downloads\arduino-cli_1.5.0_Windows_64bit\`

**Current PCA9685 channel mapping** (`backend/templates/arm_controller_ap_mode.ino`):
```cpp
const uint8_t PWM_CHANNEL[5] = {0, 2, 4, 6, 8};
// base=0, shoulder=2, elbow=4, wrist=6, gripper=8
```
*(Change these numbers to match your physical wiring without touching anything else.)*

---

## Changes Made

### 1. Servo Inversion
- Shoulder (index 1) and Wrist (index 3) are physically mounted in reverse — added inversion flags:
```cpp
const bool SERVO_INVERTED[5] = {false, true, false, true, false};
```

### 2. Pulse Range Narrowed
- Reduced from default wide range to `SERVOMIN=100 / SERVOMAX=500` to prevent servos hitting mechanical limits and glitching.

### 3. Shoulder Home at Mid-Travel
- Shoulder default changed from 0° to 90° so an inverted channel never boots at a mechanical extreme:
```cpp
const int DEFAULT_POSITIONS[5] = {180, 90, 90, 90, 0};
```

### 4. Servo Slew (Smooth Motion)
- Added `targetPos[]` vs `currentPos[]` system — servos ease toward targets instead of snapping:
```cpp
const int SLEW_STEP = 2;
const unsigned long SLEW_INTERVAL = 15;
```
- `updateServos()` steps each servo in `loop()`; `slewBlocking()` used in auto-mode helpers.
- Slider throttle: sends at most once per 50ms during drag, always sends final value on release.
- Removed broadcast echo on servo commands (was yanking sliders mid-drag).

### 5. Physical Channel Decoupling
- Logical servo indices (0–4) decoupled from physical PCA9685 channels via `PWM_CHANNEL[5]`.
- Only `writeServo()` touches the physical channel — everything else (angles, inversion, poses, sliders) uses logical index.

### 6. Base Capped at 180°
- Base servo max changed from 360° to 180° (rear half of rotation not needed):
```cpp
const int SERVO_MAX_ANGLE[5] = {180, 180, 180, 90, 180};
```
- Backend validator in `backend/routes/poses.py` updated to match.

### 7. Build Modal Fix
- Modal wouldn't close after build — `showModal()` was setting inline `style.display='block'` which overrode the `.active` class toggle. Fixed to be class-driven only.

### 8. Teach Poses — Live Arm Control
- Teach Poses tab now connects to the robot over WebSocket (`ws://192.168.4.1/ws`) so dragging sliders moves the real arm live.
- Added Connect button + status indicator to `frontend/index.html`.
- `frontend/js/ui/pose-teaching.js` handles WS connect, throttled slider sends, and final-value-on-release.
- Saved poses now reflect positions actually seen on the physical arm.

### 9. Local Blockly Bundle
- Blockly was loading from CDN — doesn't work when laptop is joined to the robot's RobotArm WiFi (no internet).
- Downloaded Blockly v13.0.0 to `frontend/lib/blockly/blockly.min.js`.
- `frontend/index.html` updated: `<script src="/static/lib/blockly/blockly.min.js"></script>`

---

## Key File Locations
| File | Purpose |
|------|---------|
| `backend/templates/arm_controller_ap_mode.ino` | ESP32 firmware template (primary hot path) |
| `backend/routes/build.py` | Build & flash API endpoints |
| `backend/routes/poses.py` | Pose CRUD + angle validation |
| `backend/services/template_engine.py` | Fills `{{POSE_DEFINITIONS}}` and `{{GENERATED_CODE}}` placeholders |
| `backend/services/storage.py` | Loads/saves poses and settings JSON |
| `frontend/index.html` | IDE layout, tabs, sliders |
| `frontend/js/api.js` | All fetch calls to backend |
| `frontend/js/ui/pose-teaching.js` | Teach Poses tab + live WS arm control |
| `frontend/js/ui/build-panel.js` | Build modal, port detection, flash |
| `frontend/lib/blockly/blockly.min.js` | Bundled Blockly v13.0.0 |

---

## Current Servo Config (in firmware template)
```cpp
#define SERVO_BASE     0
#define SERVO_SHOULDER 1
#define SERVO_ELBOW    2
#define SERVO_WRIST    3
#define SERVO_GRIPPER  4

const uint8_t PWM_CHANNEL[5] = {0, 2, 4, 6, 8};  // physical PCA9685 channels
#define SERVO_FREQ 50
#define SERVOMIN  100
#define SERVOMAX  500
const int SERVO_MAX_ANGLE[5] = {180, 180, 180, 90, 180};
const bool SERVO_INVERTED[5] = {false, true, false, true, false};
const int DEFAULT_POSITIONS[5] = {180, 90, 90, 90, 0};
```

---

## Hardware Troubleshooting Notes
- **Random movement / glitching** — was electrical: 1A supply too weak (needs ≥3A), missing common ground between adapter and ESP32 GND, and a loose wire connection on the shoulder. Fix: reseat/solder all connections.
- **Brownout under load** — high-torque joints (shoulder/elbow) sag the rail; add a 470–1000µF bulk capacitor across the PCA9685 power rails.
- **Serial monitor vs flash conflict** — only one program can hold COM3 at a time. Close the serial monitor before flashing.
- **"No serial ports found"** — board not enumerating USB. Most common cause: charge-only USB cable (no data lines). Swap to a data cable.

---

## Pending / Not Yet Done
- ESP32-CAM vision integration via UART (deferred, not started)
- Physically: re-test channel mapping after latest flash, solder loose shoulder wire, add bulk capacitor
