# Hardware Integration Testing Guide

**Purpose:** Step-by-step guide to test manual control hardware integration  
**Time Required:** 60-90 minutes (first time), 20-30 minutes (subsequent)  
**Prerequisites:** Server running, browser open, hardware available

---

## 📋 Table of Contents

1. [Pre-Test Setup](#pre-test-setup)
2. [Part 1: Software Testing (No Hardware)](#part-1-software-testing-no-hardware)
3. [Part 2: Hardware Setup](#part-2-hardware-setup)
4. [Part 3: Firmware Flashing](#part-3-firmware-flashing)
5. [Part 4: Hardware Validation](#part-4-hardware-validation)
6. [Part 5: Troubleshooting](#part-5-troubleshooting)
7. [Success Checklist](#success-checklist)

---

## Pre-Test Setup

### What You Need

**Software:**
- [ ] Python 3.8+ installed
- [ ] Server running (`python -m uvicorn backend.main:app --reload`)
- [ ] Chrome or Edge browser (for USB flashing)
- [ ] Blynk mobile app installed on phone

**Hardware (for Part 2+):**
- [ ] 1× ESP32 development board
- [ ] 5× Hobby servos (SG90 or similar)
- [ ] 1× 5-6V power supply (2A minimum)
- [ ] Jumper wires (male-to-male)
- [ ] USB cable (ESP32 to computer)
- [ ] Breadboard (optional, for easier wiring)

**Accounts:**
- [ ] Blynk account created at https://blynk.cloud
- [ ] Device template created in Blynk console
- [ ] Auth token generated

---

## Part 1: Software Testing (No Hardware)

**Time:** 15-20 minutes  
**Goal:** Verify IDE functionality without physical hardware

### Test 1.1: Server Startup

- [ ] **Step 1:** Open terminal/command prompt

- [ ] **Step 2:** Navigate to project directory
```bash
cd C:\Users\DaxAxisTangco\Documents\block-coding-robot
```

- [ ] **Step 3:** Start server
```bash
python -m uvicorn backend.main:app --reload
```

- [ ] **Step 4:** Verify output shows:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

✅ **Success:** Server starts without errors  
❌ **Fail:** See [Troubleshooting](#server-wont-start)

---

### Test 1.2: IDE Loads

- [ ] **Step 1:** Open Chrome or Edge browser

- [ ] **Step 2:** Navigate to http://localhost:8000

- [ ] **Step 3:** Verify you see:
  - Header with "🤖 Block Robot IDE"
  - Four tabs: ⚙️ Setup | 📱 Blynk Setup | 🎯 Teach Poses | 📦 Program
  - Professional, clean layout

- [ ] **Step 4:** Press F12 to open Developer Tools

- [ ] **Step 5:** Check Console tab for errors
  - Should be empty or only info messages
  - No red error messages

✅ **Success:** IDE loads cleanly  
❌ **Fail:** See [Troubleshooting](#ide-wont-load)

**Screenshot what you should see:**
```
┌──────────────────────────────────────┐
│  🤖 Block Robot IDE        [Build]   │
├──────────────────────────────────────┤
│ [⚙️ Setup] [📱 Blynk] [🎯 Poses] [📦]│
├──────────────────────────────────────┤
│                                      │
│  Robot Configuration                 │
│  Configure WiFi and Blynk...         │
│                                      │
└──────────────────────────────────────┘
```

---

### Test 1.3: Tab Switching

- [ ] **Step 1:** Click "⚙️ Setup" tab
  - Should highlight/activate
  - Setup form should be visible

- [ ] **Step 2:** Click "📱 Blynk Setup" tab
  - Tab highlights
  - Setup form disappears
  - Blynk setup content appears

- [ ] **Step 3:** Click "🎯 Teach Poses" tab
  - Tab highlights
  - Servo sliders visible

- [ ] **Step 4:** Click "📦 Program" tab
  - Tab highlights
  - Blockly workspace visible

- [ ] **Step 5:** Click back to "⚙️ Setup"
  - Returns to setup form

✅ **Success:** All tabs switch smoothly, no flickering  
❌ **Fail:** Tab content doesn't change or errors appear

---

### Test 1.4: Setup Tab - Save Settings

- [ ] **Step 1:** Click "⚙️ Setup" tab

- [ ] **Step 2:** Fill in test credentials:
```
WiFi SSID:           TestWiFi
WiFi Password:       password123
Blynk Template ID:   TMPL123456
Blynk Template Name: Test Robot
Blynk Auth Token:    abc123xyz789token
```

- [ ] **Step 3:** Click "💾 Save Settings"

- [ ] **Step 4:** Verify green success message appears:
```
✅ Settings saved successfully
```

- [ ] **Step 5:** Reload page (F5)

- [ ] **Step 6:** Check form still has your values
  - WiFi SSID shows "TestWiFi"
  - Other fields populated

✅ **Success:** Settings persist after reload  
❌ **Fail:** Settings lost on reload

---

### Test 1.5: Blynk Setup Tab - Widget Guide

- [ ] **Step 1:** Click "📱 Blynk Setup" tab

- [ ] **Step 2:** Verify you see:
  - Two buttons: "📋 Standard Setup" and "🔧 Custom Setup"
  - Both buttons clickable

- [ ] **Step 3:** Click "📋 Standard Setup"

- [ ] **Step 4:** Verify guide appears with:
  - **Left panel:** Visual mockup of Blynk app
    - Shows 5 sliders (Base, Shoulder, Elbow, Wrist, Gripper)
    - Shows 1 switch (Auto Mode)
    - Purple gradient background
  - **Right panel:** Setup steps checklist
    - 6 checkbox items (V0-V5)
    - Quick copy section with "Copy" buttons

- [ ] **Step 5:** Check one checkbox item
  - Checkbox should check/uncheck on click

- [ ] **Step 6:** Click a "Copy" button
  - Button should show "✓ Copied" briefly
  - Text should be copied to clipboard

- [ ] **Step 7:** Paste into notepad (Ctrl+V)
  - Should paste text like "V0: Base (0-180)"

- [ ] **Step 8:** Click "🔧 Custom Setup"
  - Should show "Coming in Phase 2" message
  - "← Back to Standard Setup" button appears

✅ **Success:** Blynk guide is interactive and helpful  
❌ **Fail:** Guide doesn't display or copy doesn't work

---

### Test 1.6: Web Serial API Detection

- [ ] **Step 1:** Open browser console (F12)

- [ ] **Step 2:** Type and press Enter:
```javascript
const flasher = new ESP32Flasher();
console.log('Web Serial supported:', flasher.isSupported());
```

- [ ] **Step 3:** Expected output:
  - Chrome/Edge: `Web Serial supported: true`
  - Firefox/Safari: `Web Serial supported: false`

- [ ] **Step 4:** If false, verify browser warning shows when attempting USB flash

✅ **Success:** Browser support correctly detected  
❌ **Fail:** JavaScript error appears

---

### Test 1.7: Template GPIO Pins

- [ ] **Step 1:** Open terminal

- [ ] **Step 2:** Run verification script:
```bash
python -c "
from pathlib import Path
template = Path('backend/templates/arm_controller.ino').read_text()
pins = [25, 26, 27, 32, 33]
names = ['BASE', 'SHOULDER', 'ELBOW', 'WRIST', 'GRIPPER']
for pin, name in zip(pins, names):
    assert f'const int PIN_{name} = {pin}' in template
    print(f'✓ PIN_{name} = GPIO {pin}')
print('✅ All GPIO pins correct!')
"
```

- [ ] **Step 3:** Expected output:
```
✓ PIN_BASE = GPIO 25
✓ PIN_SHOULDER = GPIO 26
✓ PIN_ELBOW = GPIO 27
✓ PIN_WRIST = GPIO 32
✓ PIN_GRIPPER = GPIO 33
✅ All GPIO pins correct!
```

✅ **Success:** GPIO pins are safe values (25-33)  
❌ **Fail:** Pins are wrong or script errors

---

## Part 2: Hardware Setup

**Time:** 20-30 minutes  
**Goal:** Wire ESP32 to servos safely

### ⚠️ Safety First

**IMPORTANT:** Never power servos from ESP32's 3.3V or 5V pins! This will damage your ESP32.

**Always use:**
- External 5-6V power supply (wall adapter, battery pack, bench supply)
- Minimum 2A capacity (servos draw ~0.4A each under load)
- Shared ground between ESP32 and power supply

---

### Test 2.1: Gather Materials

Lay out on your workbench:

- [ ] ESP32 board (check: not damaged, USB port intact)
- [ ] 5 servos (check: wires not frayed)
- [ ] Power supply (check: output is 5-6V DC, 2A+)
- [ ] 10-15 jumper wires
- [ ] USB cable for ESP32
- [ ] Multimeter (optional but recommended)

---

### Test 2.2: Power Supply Check (Optional but Recommended)

- [ ] **Step 1:** Set multimeter to DC voltage (20V range)

- [ ] **Step 2:** Connect multimeter probes to power supply output
  - Red probe → Positive (+)
  - Black probe → Ground (-)

- [ ] **Step 3:** Turn on power supply

- [ ] **Step 4:** Verify voltage reads 5.0-6.0V
  - Too low (<4.5V): Servos won't work
  - Too high (>6.5V): May damage servos

✅ **Success:** Voltage is 5-6V  
❌ **Fail:** Get different power supply

---

### Test 2.3: Servo Wiring

**Servo wire colors:**
- 🟤 Brown/Black = Ground (GND)
- 🔴 Red = Power (5V)
- 🟠 Orange/Yellow/White = Signal (PWM from ESP32)

**Wiring diagram:**

```
ESP32                   Servos (×5)
┌─────────┐            
│   GND   │──┬──────── 🟤 Brown (all servos)
│         │  │
│ GPIO 25 │──┼──────── 🟠 Base servo signal
│ GPIO 26 │──┼──────── 🟠 Shoulder servo signal
│ GPIO 27 │──┼──────── 🟠 Elbow servo signal
│ GPIO 32 │──┼──────── 🟠 Wrist servo signal
│ GPIO 33 │──┼──────── 🟠 Gripper servo signal
│         │  │
└─────────┘  │
             │
External     │
Power Supply │
┌─────────┐  │
│   5V    │──┴──────── 🔴 Red (all servos)
│   GND   │──┬──────── (shared with ESP32 GND)
└─────────┘  │
             └────────── ESP32 GND
```

**Step-by-step wiring:**

- [ ] **Step 1:** Keep power supply OFF

- [ ] **Step 2:** Connect ESP32 GND to breadboard ground rail (blue/black line)

- [ ] **Step 3:** Connect power supply GND to same ground rail

- [ ] **Step 4:** Connect all 5 servo brown wires to ground rail

- [ ] **Step 5:** Connect power supply +5V to breadboard power rail (red line)

- [ ] **Step 6:** Connect all 5 servo red wires to power rail

- [ ] **Step 7:** Connect servo signal wires to ESP32:
  - Base servo orange → GPIO 25
  - Shoulder servo orange → GPIO 26
  - Elbow servo orange → GPIO 27
  - Wrist servo orange → GPIO 32
  - Gripper servo orange → GPIO 33

- [ ] **Step 8:** Double-check connections:
  - All brown wires together on ground
  - All red wires together on power rail
  - No shorts between power and ground
  - Each signal wire goes to unique GPIO pin

- [ ] **Step 9:** Take photo of your wiring (for troubleshooting later)

✅ **Success:** Wiring complete, no shorts  
❌ **Fail:** Re-check connections, use multimeter to verify no shorts

---

### Test 2.4: Initial Power Test

- [ ] **Step 1:** ESP32 NOT connected to USB yet

- [ ] **Step 2:** Turn on external power supply

- [ ] **Step 3:** Observe servos:
  - Should NOT move yet (no control signal)
  - May hear slight hum (normal)
  - Should NOT get hot immediately

- [ ] **Step 4:** If any servo gets hot:
  - ⚠️ TURN OFF POWER IMMEDIATELY
  - Check for wiring errors
  - Verify voltage is not too high

- [ ] **Step 5:** Turn off power supply

✅ **Success:** Servos powered, no issues  
❌ **Fail:** See [Troubleshooting](#servo-problems)

---

## Part 3: Firmware Flashing

**Time:** 15-20 minutes  
**Goal:** Flash manual control firmware to ESP32

### Test 3.1: Configure Real Credentials

- [ ] **Step 1:** Get your real WiFi credentials
  - SSID: _________________
  - Password: _________________

- [ ] **Step 2:** Get Blynk auth token from https://blynk.cloud
  - Log into Blynk console
  - Go to your device template
  - Copy auth token: _________________

- [ ] **Step 3:** In IDE, go to "⚙️ Setup" tab

- [ ] **Step 4:** Fill in REAL credentials:
```
WiFi SSID:           [your network name]
WiFi Password:       [your network password]
Blynk Template ID:   [from Blynk console]
Blynk Template Name: Robot Controller
Blynk Auth Token:    [from Blynk console]
```

- [ ] **Step 5:** Click "💾 Save Settings"

- [ ] **Step 6:** Verify green success message

✅ **Success:** Real credentials saved  
❌ **Fail:** Form validation error

---

### Test 3.2: Build Firmware (if arduino-cli installed)

**Note:** This test requires arduino-cli. If not installed, skip to Test 3.3.

- [ ] **Step 1:** In IDE, look for build button
  - May be in header: "🔨 Build & Flash"
  - Or separate: "🔨 Build for Manual Mode"

- [ ] **Step 2:** Click build button

- [ ] **Step 3:** Build modal appears

- [ ] **Step 4:** Wait for compilation (30-60 seconds)

- [ ] **Step 5:** Verify success message:
```
✅ Build Successful!
Firmware size: 487 KB (or similar)
Target: ESP32 Arm Controller
```

- [ ] **Step 6:** Verify flash options appear:
  - "🔌 Flash via USB" button
  - "💾 Download .bin" button

✅ **Success:** Firmware compiles  
❌ **Fail:** See [Troubleshooting](#build-fails)

---

### Test 3.3: Flash via USB

- [ ] **Step 1:** Plug ESP32 into computer via USB

- [ ] **Step 2:** Wait for drivers to load (Windows may install drivers)

- [ ] **Step 3:** In build success modal, click "🔌 Flash via USB"

- [ ] **Step 4:** Browser permission dialog appears:
```
localhost:8000 wants to connect to a serial port

[List of COM ports]

[Cancel]  [Connect]
```

- [ ] **Step 5:** Select your ESP32 COM port
  - Usually named: "USB Serial (COM3)" or similar
  - May say "CP210x" or "CH340"

- [ ] **Step 6:** Click "Connect"

- [ ] **Step 7:** Flash modal appears with progress

- [ ] **Step 8:** Watch progress steps:
```
✅ Serial port selected
✅ Connected to ESP32
✅ Firmware downloaded (487 KB)
⏳ Flashing firmware...
   ████████████████░░  85%
   414 KB / 487 KB
```

- [ ] **Step 9:** Wait for completion (60-90 seconds)

- [ ] **Step 10:** Verify final status:
```
✅ Firmware flashed successfully!
✅ Flash complete! ESP32 is rebooting...
```

✅ **Success:** Flash completes without errors  
❌ **Fail:** See [Troubleshooting](#flash-fails)

---

### Test 3.4: Serial Monitor Check

- [ ] **Step 1:** In flash modal, look for "Serial Monitor" section

- [ ] **Step 2:** Should show ESP32 boot messages:
```
rst:0x1 (POWERON_RESET)
...
WiFi: Connecting to [YourNetwork]...
WiFi: Connected!
IP Address: 192.168.1.45
Blynk: Connecting...
Blynk: Connected!
Arm controller ready
```

- [ ] **Step 3:** Verify key messages present:
  - WiFi connects (not "Connection failed")
  - IP address assigned
  - Blynk connects (not "timeout")
  - "Arm controller ready" at end

✅ **Success:** ESP32 boots and connects  
❌ **Fail:** See [Troubleshooting](#connection-fails)

---

## Part 4: Hardware Validation

**Time:** 15-20 minutes  
**Goal:** Verify all servos work correctly

### Test 4.1: Blynk App Setup

- [ ] **Step 1:** Open Blynk app on phone

- [ ] **Step 2:** Navigate to your device
  - Should show "Online" with green indicator 🟢
  - If "Offline" 🔴, see [Troubleshooting](#blynk-offline)

- [ ] **Step 3:** Verify all 6 widgets visible:
  - Slider: Base (V0)
  - Slider: Shoulder (V1)
  - Slider: Elbow (V2)
  - Slider: Wrist (V3)
  - Slider: Gripper (V4)
  - Switch: Auto Mode (V5)

- [ ] **Step 4:** Verify Auto Mode switch is OFF
  - Should be gray/left position
  - If ON, toggle it OFF

✅ **Success:** App shows device online with all widgets  
❌ **Fail:** See [Troubleshooting](#blynk-offline)

---

### Test 4.2: Base Servo Test (GPIO 25)

- [ ] **Step 1:** Turn on external power supply

- [ ] **Step 2:** In Blynk app, find "Base" slider (V0)

- [ ] **Step 3:** Move slider to 0°
  - **Expected:** First servo (connected to GPIO 25) moves to minimum position
  - Watch which servo moves - this is your Base servo

- [ ] **Step 4:** Move slider to 90°
  - **Expected:** Base servo centers

- [ ] **Step 5:** Move slider to 180°
  - **Expected:** Base servo moves to maximum position

- [ ] **Step 6:** Move slider smoothly from 0 to 180
  - **Expected:** Servo follows smoothly, no jittering

✅ **Success:** Base servo responds correctly  
❌ **Fail:** Mark which issue:
  - [ ] No movement → See [Servo doesn't move](#servo-doesnt-move)
  - [ ] Wrong servo moves → Check wiring
  - [ ] Jittery movement → See [Servo jitters](#servo-jitters)

---

### Test 4.3: Shoulder Servo Test (GPIO 26)

- [ ] **Step 1:** Move "Shoulder" slider (V1) from 0 → 180

- [ ] **Step 2:** Verify DIFFERENT servo moves (not Base)
  - This is your Shoulder servo

- [ ] **Step 3:** Test full range smoothly

✅ **Success:** Shoulder servo responds  
❌ **Fail:** Note issue and continue

---

### Test 4.4: Elbow Servo Test (GPIO 27)

- [ ] **Step 1:** Move "Elbow" slider (V2) from 0 → 180

- [ ] **Step 2:** Verify correct servo moves

- [ ] **Step 3:** Test full range smoothly

✅ **Success:** Elbow servo responds  
❌ **Fail:** Note issue and continue

---

### Test 4.5: Wrist Servo Test (GPIO 32)

- [ ] **Step 1:** Move "Wrist" slider (V3) from 0 → 180

- [ ] **Step 2:** Verify correct servo moves

- [ ] **Step 3:** Test full range smoothly

✅ **Success:** Wrist servo responds  
❌ **Fail:** Note issue and continue

---

### Test 4.6: Gripper Servo Test (GPIO 33)

- [ ] **Step 1:** Move "Gripper" slider (V4) to 30° (open)

- [ ] **Step 2:** Verify gripper servo opens

- [ ] **Step 3:** Move slider to 90° (closed)

- [ ] **Step 4:** Verify gripper closes

- [ ] **Step 5:** Test opening and closing several times

✅ **Success:** Gripper servo responds  
❌ **Fail:** Note issue and continue

---

### Test 4.7: Validation Checklist

- [ ] **Step 1:** In flash modal, find "Hardware Validation Checklist"

- [ ] **Step 2:** Check off each item you successfully tested:
  - [ ] ESP32 shows online in Blynk app
  - [ ] Base servo responds (V0)
  - [ ] Shoulder servo responds (V1)
  - [ ] Elbow servo responds (V2)
  - [ ] Wrist servo responds (V3)
  - [ ] Gripper servo responds (V4)
  - [ ] Auto Mode switch visible (V5)

- [ ] **Step 3:** If all items checked, click "✓ All Working"
  - Should show success message

- [ ] **Step 4:** If issues, click "📝 Report Issue"
  - Select your issue type
  - Review troubleshooting advice

✅ **Success:** All 7 items checked  
❌ **Fail:** Note which items failed

---

## Part 5: Troubleshooting

### Server Won't Start

**Symptom:** `uvicorn` command fails or shows errors

**Solutions:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Check if packages installed
pip list | grep fastapi
pip list | grep uvicorn

# Reinstall if missing
pip install -r backend/requirements.txt

# Check if port 8000 is in use
netstat -ano | findstr :8000

# Use different port if needed
python -m uvicorn backend.main:app --port 8001
```

---

### IDE Won't Load

**Symptom:** Browser shows blank page or errors

**Solutions:**
1. Hard refresh: `Ctrl + Shift + R`
2. Clear browser cache
3. Check server is running: `curl http://localhost:8000/health`
4. Check browser console (F12) for JavaScript errors
5. Try different browser (Chrome/Edge)

---

### Build Fails

**Symptom:** Compilation errors in build modal

**Common causes:**

1. **arduino-cli not installed:**
   ```bash
   # Install arduino-cli
   choco install arduino-cli  # Windows
   brew install arduino-cli    # macOS
   
   # Setup ESP32
   arduino-cli core install esp32:esp32
   arduino-cli lib install "Blynk"
   arduino-cli lib install "ESP32Servo"
   ```

2. **Template syntax error:**
   - Check `backend/templates/arm_controller.ino`
   - Verify no missing `}` or `;`

3. **Missing libraries:**
   ```bash
   arduino-cli lib install "Blynk"
   arduino-cli lib install "ESP32Servo"
   ```

---

### Flash Fails

**Symptom:** Flash stops with error

**Solutions:**

1. **USB permission denied:**
   - Click "Allow" when browser asks
   - Retry flash

2. **Wrong COM port:**
   - Unplug/replug ESP32
   - Try selecting different port
   - Check Device Manager (Windows)

3. **ESP32 not detected:**
   - Install ESP32 USB drivers (CP210x or CH340)
   - Try different USB cable
   - Try different USB port on computer

4. **Flash timeout:**
   - Put ESP32 in flash mode manually:
     - Hold BOOT button
     - Press and release RESET button
     - Release BOOT button
   - Retry flash

---

### Connection Fails

**Symptom:** ESP32 boots but WiFi/Blynk fails

**WiFi won't connect:**
```
Check:
- SSID is correct (case-sensitive)
- Password is correct
- Network is 2.4GHz (not 5GHz)
- ESP32 is in range of router
- Network allows new devices
```

**Blynk offline:**
```
Check:
- Auth token is correct (copy/paste carefully)
- Internet connection works
- Blynk services are up (check blynk.cloud)
- Firewall not blocking ESP32
```

---

### Servo Doesn't Move

**Symptom:** Slider moves but servo doesn't respond

**Checklist:**

- [ ] External power supply is ON
- [ ] Power supply voltage is 5-6V (check with multimeter)
- [ ] Servo red wire connected to power rail
- [ ] Servo brown wire connected to ground rail
- [ ] ESP32 GND connected to power supply GND
- [ ] Servo signal wire connected to correct GPIO
- [ ] Try swapping with a servo you know works
- [ ] Try connecting to different GPIO pin

**Specific GPIO issues:**
- Wrong wire color? Check your servo's datasheet
- GPIO already in use? We picked safe pins (25-33)
- Servo damaged? Test with Arduino or different controller

---

### Servo Jitters

**Symptom:** Servo shakes/vibrates instead of smooth movement

**Causes:**

1. **Insufficient power:**
   - Upgrade to higher amperage power supply (3-5A)
   - Add 1000µF capacitor across power rails

2. **Noisy power supply:**
   - Use regulated power supply (not unregulated)
   - Add 100µF capacitor near each servo

3. **Loose wiring:**
   - Check all connections are solid
   - Solder connections if using for demo

4. **Multiple servos moving:**
   - Current draw too high
   - Move one servo at a time for now
   - Upgrade power supply for simultaneous movement

---

### Blynk Offline

**Symptom:** Blynk app shows device offline 🔴

**Step-by-step diagnosis:**

1. **Check ESP32 powered:**
   - ESP32 LED should be on
   - If not, check USB or external power

2. **Check serial monitor:**
   ```
   Look for:
   "WiFi: Connected!" → Good
   "Blynk: Connected!" → Good
   
   If stuck at "WiFi: Connecting..." → WiFi issue
   If stuck at "Blynk: Connecting..." → Blynk issue
   ```

3. **Verify auth token:**
   - Copy token from Blynk console
   - Paste into IDE Setup tab
   - Re-flash firmware
   - Should match EXACTLY (no spaces, full string)

4. **Check Blynk app:**
   - Logged into correct account?
   - Correct device selected?
   - App has internet connection?

5. **Reset ESP32:**
   - Unplug power
   - Wait 5 seconds
   - Plug back in
   - Watch serial monitor for boot

---

## Success Checklist

### ✅ Phase 1: Software (No Hardware)
- [ ] Server starts successfully
- [ ] IDE loads in browser
- [ ] All 4 tabs switch smoothly
- [ ] Settings save and persist
- [ ] Blynk Setup guide displays with mockup
- [ ] Copy buttons work
- [ ] Web Serial API detected
- [ ] GPIO pins are 25-33 in template

### ✅ Phase 2: Hardware Setup
- [ ] Power supply voltage verified (5-6V)
- [ ] All servos wired correctly
- [ ] Ground shared between ESP32 and power supply
- [ ] Signal wires to GPIO 25, 26, 27, 32, 33
- [ ] No shorts detected
- [ ] Photo taken of wiring

### ✅ Phase 3: Firmware Flashing
- [ ] Real WiFi/Blynk credentials entered
- [ ] Firmware builds successfully
- [ ] Flash via USB completes
- [ ] ESP32 boots and connects to WiFi
- [ ] ESP32 connects to Blynk
- [ ] Serial monitor shows "Arm controller ready"

### ✅ Phase 4: Hardware Validation
- [ ] Blynk app shows device online
- [ ] All 6 widgets visible in app
- [ ] Auto Mode switch is OFF
- [ ] Base servo responds to V0
- [ ] Shoulder servo responds to V1
- [ ] Elbow servo responds to V2
- [ ] Wrist servo responds to V3
- [ ] Gripper servo responds to V4
- [ ] All servos move smoothly
- [ ] Validation checklist completed

---

## Next Steps

**After successful testing:**

1. **Document your setup:**
   - Take photos of final wiring
   - Note any servo mechanical limits
   - Record safe angle ranges
   - Save in project documentation

2. **Proceed to Teach Poses:**
   - Use manual control to teach robot positions
   - Save poses for your program
   - See `QUICKSTART.md` for details

3. **Phase 2 Integration:**
   - Block program execution (automatic mode)
   - Camera/vision integration
   - Advanced features

---

## Test Results Form

**Test Date:** _______________  
**Tester Name:** _______________  
**Hardware:** ESP32 model: _______________ | Servo model: _______________

**Results:**

| Phase | Status | Time Taken | Notes |
|-------|--------|------------|-------|
| Software Testing | ☐ Pass ☐ Fail | _______ min | |
| Hardware Setup | ☐ Pass ☐ Fail | _______ min | |
| Firmware Flashing | ☐ Pass ☐ Fail | _______ min | |
| Hardware Validation | ☐ Pass ☐ Fail | _______ min | |

**Issues Found:**
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

**Servos Working:**
- [ ] Base (GPIO 25)
- [ ] Shoulder (GPIO 26)
- [ ] Elbow (GPIO 27)
- [ ] Wrist (GPIO 32)
- [ ] Gripper (GPIO 33)

**Overall Assessment:**
☐ Ready for student use  
☐ Needs fixes before demo  
☐ Major issues found

---

**End of Testing Guide**

*For questions or issues not covered here, consult:*
- `docs/BLYNK_SETUP_GUIDE.md` - Detailed Blynk configuration
- `docs/HARDWARE_PINOUT.md` - GPIO reference
- `docs/QUICKSTART.md` - General IDE usage
