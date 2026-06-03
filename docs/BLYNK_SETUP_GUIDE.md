# Blynk Mobile App Setup Guide

This guide walks you through setting up the Blynk mobile app to control your LEGO robot arm. Follow these steps to configure the virtual pins and widgets needed for manual control and auto mode.

## Prerequisites

Before you start, make sure you have:

- **Blynk mobile app** installed (iOS or Android)
- **Blynk account** created (free account is sufficient)
- **Auth Token** from your web app's Blynk Setup tab
- **ESP32 flashed** with the arm controller firmware
- **WiFi credentials** configured in the firmware

## Standard Setup

### Step 1: Create New Project

1. Open the Blynk mobile app
2. Tap **"+ New Project"**
3. Give it a name (e.g., "LEGO Robot Arm")
4. **Device:** Select "ESP32"
5. **Connection Type:** WiFi
6. Tap **"Create"**
7. You'll receive an **Auth Token** via email - paste this into your web app's Blynk Setup tab

### Step 2: Add Base Servo Slider (V0)

1. Tap anywhere on the blank canvas to open the widget box
2. Select **"Slider"**
3. Tap the slider widget to configure:
   - **Name:** Base Servo
   - **Pin:** V0 (Virtual)
   - **Min:** 0
   - **Max:** 180
   - **Send on Release:** OFF (for smooth control)
4. Tap back arrow to save

### Step 3: Add Shoulder Servo Slider (V1)

1. Add another **Slider** widget
2. Configure:
   - **Name:** Shoulder Servo
   - **Pin:** V1 (Virtual)
   - **Min:** 0
   - **Max:** 180
   - **Send on Release:** OFF
3. Save and return

### Step 4: Add Elbow Servo Slider (V2)

1. Add another **Slider** widget
2. Configure:
   - **Name:** Elbow Servo
   - **Pin:** V2 (Virtual)
   - **Min:** 0
   - **Max:** 180
   - **Send on Release:** OFF
3. Save and return

### Step 5: Add Wrist Servo Slider (V3)

1. Add another **Slider** widget
2. Configure:
   - **Name:** Wrist Servo
   - **Pin:** V3 (Virtual)
   - **Min:** 0
   - **Max:** 180
   - **Send on Release:** OFF
3. Save and return

### Step 6: Add Gripper Servo Slider (V4)

1. Add another **Slider** widget
2. Configure:
   - **Name:** Gripper Servo
   - **Pin:** V4 (Virtual)
   - **Min:** 0
   - **Max:** 180
   - **Send on Release:** OFF
3. Save and return

### Step 7: Add Auto Mode Switch (V5)

1. Add a **"Button"** widget (or **"Switch"** if available)
2. Configure:
   - **Name:** Auto Mode
   - **Pin:** V5 (Virtual)
   - **Mode:** Switch (toggle)
   - **Values:** 0 (OFF) and 1 (ON)
3. Save and return

### Step 8: Save & Exit

1. Tap the **Play** button (▶️) in the top right corner
2. Your project is now live!
3. The ESP32 should show as **"Online"** if connected properly

## Widget Summary Table

Quick reference for all virtual pin assignments:

| Widget Name | Pin | Type | Range | Purpose |
|-------------|-----|------|-------|---------|
| Base Servo | V0 | Slider | 0-180 | Controls base rotation |
| Shoulder Servo | V1 | Slider | 0-180 | Controls shoulder joint |
| Elbow Servo | V2 | Slider | 0-180 | Controls elbow joint |
| Wrist Servo | V3 | Slider | 0-180 | Controls wrist rotation |
| Gripper Servo | V4 | Slider | 0-180 | Controls gripper open/close |
| Auto Mode | V5 | Switch | 0 or 1 | Toggles between manual and auto mode |

## Testing Your Setup

### Manual Mode Test

1. Make sure **Auto Mode** switch is **OFF** (0)
2. Move each slider one at a time and verify the corresponding servo moves:
   - **V0 (Base):** Should rotate the entire arm left/right
   - **V1 (Shoulder):** Should move the first joint up/down
   - **V2 (Elbow):** Should move the second joint up/down
   - **V3 (Wrist):** Should rotate the wrist
   - **V4 (Gripper):** Should open/close the gripper

3. If a servo doesn't move, check:
   - Power supply is connected
   - Servo is connected to the correct GPIO pin
   - ESP32 shows "Online" in Blynk app

### Auto Mode Instructions

1. Create your block code program in the web app
2. Click **"Build & Flash"** to compile and flash the firmware
3. In Blynk app, toggle **Auto Mode** to **ON** (1)
4. Your programmed sequence should execute automatically
5. Toggle back to **OFF** (0) to regain manual control

## Troubleshooting

### Device Shows "Offline"

**Possible causes:**
- ESP32 not powered on or connected to WiFi
- Wrong Auth Token in firmware
- WiFi credentials incorrect

**Solutions:**
1. Check ESP32 power LED is on
2. Verify Auth Token matches between Blynk app and firmware settings
3. Re-flash firmware with correct WiFi credentials
4. Check router allows IoT devices (some guest networks block device-to-device communication)

### Sliders Don't Move Servos

**Possible causes:**
- Servos not receiving power
- Wrong GPIO pin assignments
- Servo wiring loose

**Solutions:**
1. Check external power supply is connected to servos (NOT from ESP32)
2. Verify ground is shared between ESP32 and servo power supply
3. Check each servo is connected to correct GPIO pin (see HARDWARE_PINOUT.md)
4. Try moving sliders slowly - servos may need time to respond
5. Monitor serial output for error messages (see FLASH_INSTRUCTIONS.md)

### Wrong Servo Moves

**Problem:** Moving V0 slider moves the shoulder instead of base

**Solution:**
- Servo wires are swapped - check connections against HARDWARE_PINOUT.md
- Verify physical servo labels match virtual pin assignments
- Update firmware if GPIO pin constants are wrong

### Auto Mode Doesn't Work

**Possible causes:**
- Student program has errors
- Auto Mode switch not set to 1
- Firmware didn't flash successfully

**Solutions:**
1. Toggle Auto Mode switch to ON (1) in Blynk app
2. Check serial monitor for error messages during program execution
3. Re-build and flash firmware from web app
4. Verify servo sliders work in manual mode first

## Quick Reference Card

Print this section and keep it near your robot:

```
┌─────────────────────────────────────────┐
│    LEGO ROBOT ARM - BLYNK PINS          │
├─────────────────────────────────────────┤
│  Servo Controls (Sliders 0-180)         │
│  ───────────────────────────────        │
│  V0: Base Servo                         │
│  V1: Shoulder Servo                     │
│  V2: Elbow Servo                        │
│  V3: Wrist Servo                        │
│  V4: Gripper Servo                      │
│                                         │
│  Mode Control (Switch 0/1)              │
│  ──────────────────────                 │
│  V5: Auto Mode (0=Manual, 1=Auto)       │
│                                         │
│  Tips:                                  │
│  • Turn OFF Auto Mode for manual control│
│  • Turn ON Auto Mode to run your program│
│  • Check "Offline"? Verify WiFi & power │
└─────────────────────────────────────────┘
```

## Related Documentation

- **[HARDWARE_PINOUT.md](HARDWARE_PINOUT.md)** - GPIO pin assignments and wiring
- **[FLASH_INSTRUCTIONS.md](FLASH_INSTRUCTIONS.md)** - How to flash firmware to ESP32
- **[ARDUINO_CLI_SETUP.md](ARDUINO_CLI_SETUP.md)** - Arduino CLI installation
- **[HARDWARE_INTEGRATION_TEST_GUIDE.md](HARDWARE_INTEGRATION_TEST_GUIDE.md)** - Complete testing procedures

## Need Help?

If you're still having issues:

1. Check the serial monitor output (see FLASH_INSTRUCTIONS.md)
2. Verify all prerequisites are met
3. Review the Hardware Integration Test Guide for systematic troubleshooting
4. Make sure your WiFi network is 2.4GHz (ESP32 doesn't support 5GHz)

---

**Note:** This guide assumes you're using the standard firmware template. If you've customized GPIO pins or virtual pin assignments, adjust the instructions accordingly.
