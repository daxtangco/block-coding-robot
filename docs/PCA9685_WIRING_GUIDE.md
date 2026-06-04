# PCA9685 Servo Driver Wiring Guide

## What is the PCA9685?

The PCA9685 is a 16-channel PWM servo driver board that controls multiple servos using only 2 wires (I2C) from your ESP32. This is much cleaner than connecting each servo directly!

---

## 📋 What You Need

- ESP32 development board
- PCA9685 servo driver board
- 5 servo motors
- External 5V power supply (2A or higher)
- Jumper wires
- USB cable for ESP32

---

## 🔌 Wiring Connections

### 1. Connect ESP32 to PCA9685 (I2C Communication)

Connect these 4 wires between ESP32 and PCA9685:

```
ESP32 Pin → PCA9685 Pin
─────────────────────────
GPIO 21 (SDA) → SDA
GPIO 22 (SCL) → SCL
GND           → GND
3.3V          → VCC (logic power)
```

**IMPORTANT:** The VCC pin on PCA9685 is for LOGIC power (3.3V), NOT servo power!

---

### 2. Connect Power Supply to PCA9685

The PCA9685 has separate power terminals for servos:

```
External 5V Power Supply → PCA9685
──────────────────────────────────
(+) Positive 5V  → V+ (terminal block)
(-) Ground       → GND (terminal block)
```

**Power Supply Requirements:**
- Voltage: 5V (NOT 9V or 12V!)
- Current: At least 2A (2000mA)
- 5 servos can draw 1.5-2A when moving

---

### 3. Connect Servos to PCA9685

Plug each servo into PCA9685 channels:

```
Servo Position → PCA9685 Channel
────────────────────────────────
Base (rotation)  → Channel 0
Shoulder         → Channel 1
Elbow            → Channel 2
Wrist            → Channel 3
Gripper          → Channel 4
```

**Servo Connector Orientation:**
Each servo has 3 wires (brown/red/orange or black/red/white).
Plug them into the PCA9685 with:
- **Brown/Black** (ground) on the outside edge
- **Red** (power) in the middle
- **Orange/Yellow/White** (signal) on the inside

The PCA9685 board usually has labels showing the correct orientation.

---

## 📊 Complete Wiring Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    ESP32 + PCA9685 Setup                     │
└──────────────────────────────────────────────────────────────┘

    ESP32                         PCA9685 Board
  ┌─────────┐                   ┌───────────────┐
  │         │                   │               │
  │  GPIO21 ├───────SDA─────────┤ SDA           │
  │  GPIO22 ├───────SCL─────────┤ SCL           │
  │   3.3V  ├──────VCC──────────┤ VCC (logic)   │
  │   GND   ├──────GND──────────┤ GND           │
  │         │                   │               │
  │   USB   │◄─── Computer      │  V+  GND      │
  └─────────┘                   └───┬────┬──────┘
                                    │    │
                      External 5V ──┘    │
                      Power Supply ──────┘
                      (2A minimum)

                    Servo Channels (0-4):
                   ┌──────────────────────┐
                   │ [0] Base             │
                   │ [1] Shoulder         │
                   │ [2] Elbow            │
                   │ [3] Wrist            │
                   │ [4] Gripper          │
                   └──────────────────────┘
```

---

## ✅ Wiring Checklist

Before powering on, verify:

### ESP32 to PCA9685 I2C:
- [ ] GPIO 21 (SDA) → PCA9685 SDA
- [ ] GPIO 22 (SCL) → PCA9685 SCL
- [ ] ESP32 3.3V → PCA9685 VCC (logic power)
- [ ] ESP32 GND → PCA9685 GND

### Power Supply to PCA9685:
- [ ] External 5V (+) → PCA9685 V+ terminal
- [ ] External 5V (-) → PCA9685 GND terminal
- [ ] Power supply is 5V (check label!)
- [ ] Power supply can provide 2A or more

### Servos to PCA9685:
- [ ] Base servo → Channel 0
- [ ] Shoulder servo → Channel 1
- [ ] Elbow servo → Channel 2
- [ ] Wrist servo → Channel 3
- [ ] Gripper servo → Channel 4
- [ ] All servos plugged in correct orientation (brown/black on edge)

### ESP32:
- [ ] USB cable connected to computer

---

## 🔧 Arduino Library Required

You need the **Adafruit PWM Servo Driver** library:

### Install in Arduino IDE:
1. Open Arduino IDE
2. Go to: **Sketch → Include Library → Manage Libraries**
3. Search for: `Adafruit PWM Servo Driver`
4. Install: **Adafruit PWM Servo Driver Library**
5. It will also install: **Adafruit BusIO** (dependency)

---

## 🐛 Troubleshooting

### Servos Don't Move
**Check:**
- [ ] External 5V power supply is ON
- [ ] V+ and GND connected to PCA9685 terminal block
- [ ] Power supply provides 2A or more
- [ ] I2C wires (SDA/SCL) connected correctly
- [ ] Servos plugged into correct channels (0-4)

### I2C Communication Errors
**Check:**
- [ ] SDA → GPIO 21 (not switched with SCL)
- [ ] SCL → GPIO 22 (not switched with SDA)
- [ ] VCC connected to ESP32 3.3V (not 5V)
- [ ] Common ground between ESP32 and PCA9685

### Servo Jitters or Acts Erratic
**Check:**
- [ ] Power supply provides enough current (2A minimum)
- [ ] Add 100-1000µF capacitor across V+ and GND
- [ ] Check all wire connections are secure
- [ ] Reduce number of servos moving simultaneously

### Wrong Servo Moves
**Check:**
- [ ] Servos plugged into correct channels (0-4 as shown above)
- [ ] Firmware uploaded correctly with PCA9685 version

### Servo Doesn't Reach Full Range (0-180°)
**In the firmware, adjust these values:**
```cpp
#define SERVOMIN  150  // Try: 120-200
#define SERVOMAX  600  // Try: 550-650
```
Different servo brands need different pulse lengths.

---

## 📸 Testing Steps

1. **Power everything on**
   - Plug in ESP32 USB
   - Turn on external 5V power supply

2. **Open Serial Monitor** (115200 baud)
   - Should see: "PCA9685 initialized"
   - Should see: "Arm controller ready"

3. **Test in Blynk app**
   - Device should show "Online"
   - Move each slider (V0-V4)
   - Each servo should respond

4. **Check serial monitor for servo movements**
   - Should print: "Base: 90" when you move Base slider
   - Should print: "Shoulder: 120" when you move Shoulder slider
   - etc.

---

## ⚡ Advantages of PCA9685

✅ **Only 2 GPIO pins used** (I2C) instead of 5
✅ **Cleaner wiring** - one board, all servos
✅ **Better power management** - dedicated servo power
✅ **More precise control** - 12-bit PWM resolution
✅ **Can control up to 16 servos** if you expand later
✅ **Consistent timing** - hardware PWM, no jitter

---

## 🔗 Related Documentation

- Main testing guide: `HARDWARE_TEST_PROCEDURE.md`
- Blynk setup: `docs/BLYNK_SETUP_GUIDE.md`
- Original GPIO wiring: `docs/HARDWARE_PINOUT.md` (if you switch back)

---

**Ready to test?** Follow the steps in `HARDWARE_TEST_PROCEDURE.md` using this wiring setup!
