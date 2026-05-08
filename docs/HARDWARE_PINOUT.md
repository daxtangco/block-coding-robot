# Hardware Pinout Reference

**STATUS:** ⚠️ Placeholder - To be documented during hardware testing

This document will contain the actual GPIO pin assignments after testing with the physical robot.

## ESP32 Arm Controller

### Servo Connections

| Servo | GPIO Pin | Notes |
|-------|----------|-------|
| Base | **TBD** (placeholder: GPIO 12) | Base rotation |
| Shoulder | **TBD** (placeholder: GPIO 13) | Shoulder joint |
| Elbow | **TBD** (placeholder: GPIO 14) | Elbow joint |
| Wrist | **TBD** (placeholder: GPIO 15) | Wrist rotation |
| Gripper | **TBD** (placeholder: GPIO 16) | Claw open/close |

### Power Supply

- **Servo Power**: External 5-6V power supply (NOT from ESP32)
  - Ground must be shared between ESP32 and servo power supply
  - Servos draw too much current for USB power
- **ESP32 Power**: USB or VIN (5V)

### Wiring Diagram

```
[To be added after hardware testing]
```

## ESP32-CAM Vision Board

### Camera Module
- Pre-wired on AI-Thinker ESP32-CAM board
- OV2640 camera sensor

### Power
- 5V via USB-to-serial adapter (FTDI)
- Or external 5V power supply to 5V and GND pins

### Flash Mode Pins
- **GPIO 0 to GND**: Enter flash mode
- **RESET button**: After connecting GPIO 0, press reset to enter flash mode

## Testing Checklist

During week 1 hardware integration, verify:

- [ ] Each servo moves when commanded via Blynk sliders
- [ ] No servo draws excessive current (measure with multimeter)
- [ ] Arm can hold position at full extension
- [ ] Gripper can hold a lego block
- [ ] Camera captures clear images under demo lighting
- [ ] Both ESP32s connect to Blynk simultaneously
- [ ] Virtual pins V10/V11 successfully transmit from ESP32-CAM to arm ESP32

## Safety Notes

- **NEVER** power servos from ESP32's 3.3V or 5V pins - they will damage the board
- Always use external power supply with adequate current rating (minimum 2A for 5 servos)
- Add a 1000µF capacitor across servo power supply to smooth current spikes
- If servos jitter or ESP32 reboots randomly, check power supply capacity

## Pin Assignments Update Procedure

After documenting actual pins:

1. Update this file with real GPIO numbers
2. Update `backend/templates/arm_controller.ino`:
   ```cpp
   const int PIN_BASE = [actual pin];
   const int PIN_SHOULDER = [actual pin];
   // etc.
   ```
3. Test compile firmware with new pins
4. Flash and verify all servos respond correctly
