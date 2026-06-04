# Hardware Testing Procedure - Manual Control

## Quick Reference: Your Blynk Credentials

Fill these in after getting them from Blynk console:

```
Template ID: TMPL____________
Template Name: ___________________
Auth Token: ________________________________
WiFi SSID: ___________________
WiFi Password: ___________________
```

---

## Testing Procedure

### Phase 1: Enter Credentials in IDE

1. **Start the server:**
   ```bash
   cd C:\Users\DaxAxisTangco\Documents\block-coding-robot
   python -m uvicorn backend.main:app --reload
   ```

2. **Open IDE:** http://localhost:8000

3. **Enter your credentials in Setup tab:**
   - WiFi SSID (your 2.4GHz WiFi name)
   - WiFi Password
   - Blynk Template ID (from Blynk console)
   - Blynk Template Name (e.g., "Robot Arm Controller")
   - Blynk Auth Token (from Blynk console)
   - Click **"Save Settings"**
   - ✅ Green success message should appear

---

### Phase 2: Physical Connections

#### Servo Wiring
Connect each servo's **signal wire** (orange/yellow) to ESP32:

```
Servo Position    →  ESP32 GPIO Pin
──────────────────────────────────
Base (rotation)   →  GPIO 25
Shoulder          →  GPIO 26
Elbow             →  GPIO 27
Wrist             →  GPIO 32
Gripper           →  GPIO 33
```

#### Power Wiring
**CRITICAL - Do this correctly or you'll damage your ESP32:**

```
External 5V Supply (+)  →  All servo red wires
External 5V Supply (-)  →  All servo brown wires
External 5V Supply (-)  →  ESP32 GND pin (MUST SHARE GROUND!)
ESP32 USB              →  Connect to computer for power + programming
```

#### Safety Checklist
- [ ] External power supply is 5V (NOT 9V or 12V!)
- [ ] Power supply can provide 2A or more
- [ ] Ground is shared between ESP32 and power supply
- [ ] Servo signal wires go to correct GPIO pins
- [ ] No servo power connected to ESP32 VIN or 5V pins

---

### Phase 3: Build & Flash Firmware

**Note:** The build system integration may not be fully implemented yet. You have two options:

#### Option A: Using IDE (if build button exists)
1. Click **"🔨 Build"** button
2. Wait for compilation to complete
3. Click **"Flash via USB"** button
4. Select ESP32 port (e.g., COM3)
5. Wait for flash to complete

#### Option B: Manual Build (fallback)
If the build button doesn't exist yet, you'll need to:

1. **Generate firmware manually:**
   ```bash
   cd backend
   python generate_firmware.py
   ```

2. **Flash using esptool or arduino-cli:**
   ```bash
   # If you have arduino-cli installed:
   arduino-cli upload -p COM3 --fqbn esp32:esp32:esp32
   ```

---

### Phase 4: Verify ESP32 Connection

1. **Open Serial Monitor:**
   - Arduino IDE: Tools → Serial Monitor (115200 baud)
   - Or use: `python -m serial.tools.miniterm COM3 115200`

2. **Check boot messages (should see):**
   ```
   Arm controller ready
   WiFi: Connecting...
   WiFi: Connected!
   IP: 192.168.x.x
   Blynk: Connecting...
   Blynk: Connected!
   Arm controller ready
   ```

3. **If connection fails:**
   - Check WiFi SSID/password are correct
   - Make sure using 2.4GHz WiFi (not 5GHz)
   - Check auth token is correct
   - See troubleshooting section below

---

### Phase 5: Test Blynk App Connection

1. **Open Blynk app on phone**
2. **Check device status:**
   - Device should show **"Online"** with green indicator
   - If offline, check serial monitor for errors

3. **Verify widgets:**
   - [ ] Base slider (V0) visible
   - [ ] Shoulder slider (V1) visible
   - [ ] Elbow slider (V2) visible
   - [ ] Wrist slider (V3) visible
   - [ ] Gripper slider (V4) visible
   - [ ] Auto Mode switch (V5) visible

---

### Phase 6: Test Manual Servo Control

**IMPORTANT:** Ensure **Auto Mode switch is OFF** (manual control mode)

#### Test Base Servo (V0)
1. Move **Base slider** to 0°
   - ✅ Base servo should move to minimum position
2. Move slider to 180°
   - ✅ Base servo should move to maximum position
3. Move slider to 90°
   - ✅ Base servo should center

#### Test Shoulder Servo (V1)
1. Move **Shoulder slider** slowly from 0° to 180°
   - ✅ Correct servo responds (not Base!)
   - ✅ Movement is smooth, no jittering

#### Test Elbow Servo (V2)
1. Move **Elbow slider** slowly from 0° to 180°
   - ✅ Correct servo responds
   - ✅ Movement is smooth

#### Test Wrist Servo (V3)
1. Move **Wrist slider** slowly from 0° to 180°
   - ✅ Correct servo responds
   - ✅ Movement is smooth

#### Test Gripper Servo (V4)
1. Move **Gripper slider** to 30° (open)
   - ✅ Gripper opens
2. Move slider to 90° (closed)
   - ✅ Gripper closes

#### Test Auto Mode Switch (V5)
1. Toggle **Auto Mode switch** to ON
   - ✅ Serial monitor shows "Auto mode ON"
   - ✅ Sliders now disabled (arm will run programmed sequence)
2. Toggle back to OFF
   - ✅ Serial monitor shows "Manual mode ON"
   - ✅ Sliders work again

---

## 🐛 Troubleshooting

### ESP32 Won't Connect to WiFi
- [ ] Check WiFi SSID is correct (case-sensitive)
- [ ] Check WiFi password is correct
- [ ] Verify you're using 2.4GHz WiFi (ESP32 doesn't support 5GHz)
- [ ] Move ESP32 closer to router
- [ ] Check serial monitor for specific error messages

### Blynk Shows "Offline"
- [ ] Verify auth token is correct (copy/paste from console)
- [ ] Check template ID matches
- [ ] Ensure ESP32 has internet connection (ping test)
- [ ] Try restarting Blynk app
- [ ] Check Blynk cloud status: https://status.blynk.cc

### One Servo Doesn't Move
- [ ] Check GPIO wiring for that specific servo
- [ ] Verify servo gets 5V power (test with multimeter)
- [ ] Try swapping with a working servo to isolate issue
- [ ] Check servo isn't mechanically stuck
- [ ] Test servo with different GPIO pin

### All Servos Don't Move
- [ ] **Check external 5V power supply is connected and ON**
- [ ] Verify power supply outputs 5V (test with multimeter)
- [ ] Check ground is shared between ESP32 and power supply
- [ ] Ensure power supply can provide 2A+ (5 servos need ~1.5-2A)
- [ ] Check all servo power wires (red) connected to +5V
- [ ] Check all servo ground wires (brown) connected to GND

### Wrong Servo Moves
- [ ] Verify GPIO pin assignments match your physical connections
- [ ] Check servo signal wires aren't crossed
- [ ] Re-flash firmware if you changed pin assignments

### Servo Jitters/Vibrates
- [ ] Power supply might be insufficient (try 3A supply)
- [ ] Add capacitor (100-1000µF) across power supply
- [ ] Reduce number of servos moving simultaneously
- [ ] Check for loose connections

---

## ✅ Success Checklist

**Manual Control Phase 1 is working when:**
- [ ] ESP32 connects to WiFi automatically
- [ ] ESP32 connects to Blynk cloud
- [ ] Device shows "Online" in Blynk app
- [ ] All 5 servos respond to their respective sliders
- [ ] Servos move smoothly without jittering
- [ ] Auto Mode switch toggles correctly
- [ ] No errors in serial monitor
- [ ] Student can control arm within 5 minutes of setup

---

## 📸 Document Your Test

Take photos/videos of:
1. Your wiring setup (for reference)
2. Blynk app with all widgets
3. Servos moving in response to sliders
4. Serial monitor showing successful connection

---

## Next Steps After Successful Test

Once manual control works:
1. Document any issues you encountered
2. Test the "Teach Poses" functionality
3. Program a simple pick-and-place sequence
4. Test Auto Mode with programmed sequence
5. Try the vision integration (Phase 2)

---

**Need help?** Check:
- `docs/BLYNK_SETUP_GUIDE.md` - Widget configuration details
- `docs/HARDWARE_PINOUT.md` - Pin assignments reference
- `docs/MANUAL_TEST_CHECKLIST.md` - Complete testing checklist
