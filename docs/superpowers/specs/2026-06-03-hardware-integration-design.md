# Hardware Integration Design - Manual Control Phase

**Date:** 2026-06-03  
**Phase:** Manual Control (Phase 1 of 2)  
**Status:** Approved for Implementation

---

## Overview

This design documents the integration between the block coding IDE and physical ESP32/robotic arm hardware, focusing specifically on **manual control mode** as the first phase of hardware integration. Students will learn to configure, build, flash, and test the robot using Blynk mobile app sliders before progressing to block-based programming.

### Goals

1. Enable students to flash firmware from the web IDE to ESP32 hardware
2. Configure Blynk mobile app for manual servo control
3. Validate all hardware components work correctly
4. Establish foundation for automatic mode (block programming) in Phase 2

### Non-Goals (Deferred to Phase 2)

- Block program execution (auto mode)
- Camera/vision integration
- OTA (Over-The-Air) firmware updates
- Advanced error recovery

---

## User Journey

### Complete Student Workflow

**Day 1: Initial Setup & Hardware Validation**

1. **Open IDE** → Navigate to http://localhost:8000
2. **Setup Tab** → Enter WiFi credentials and Blynk auth token
3. **Blynk Setup Tab** → Follow interactive guide to configure mobile app widgets
4. **Build Firmware** → Click "Build for Manual Mode"
5. **Flash via USB** → Use Web Serial API to upload firmware
6. **Test in Blynk** → Control servos with sliders (V0-V4)
7. **Validate** → Confirm all 5 servos respond correctly

**Success Criteria:** All servos respond to Blynk app sliders, ESP32 shows "online"

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────┐
│                 IDE (Browser)                       │
│  ┌─────────┬───────────────┬─────────────┬───────┐ │
│  │ Setup   │ Blynk Setup   │ Teach Poses │ Program│ │
│  └─────────┴───────────────┴─────────────┴───────┘ │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP API
                   ↓
┌─────────────────────────────────────────────────────┐
│              Backend (FastAPI)                      │
│  • Template engine                                  │
│  • arduino-cli wrapper                              │
│  • Build orchestration                              │
└──────────────────┬──────────────────────────────────┘
                   │ Compile
                   ↓
┌─────────────────────────────────────────────────────┐
│            Compiled Firmware (.bin)                 │
└──────────────────┬──────────────────────────────────┘
                   │ Web Serial API
                   ↓
┌─────────────────────────────────────────────────────┐
│              ESP32 Hardware                         │
│  • WiFi connection                                  │
│  • Blynk client                                     │
│  • 5 servo controllers                              │
└──────────────────┬──────────────────────────────────┘
                   │ Blynk Cloud
                   ↓
┌─────────────────────────────────────────────────────┐
│            Blynk Mobile App                         │
│  • 5 sliders (V0-V4) for servos                    │
│  • 1 switch (V5) for auto mode                     │
└─────────────────────────────────────────────────────┘
```

### Data Flow

**Configuration Flow:**
```
User Input (Setup Tab) 
  → settings.json 
  → Template Engine 
  → arm_controller.ino 
  → arduino-cli 
  → firmware.bin
```

**Runtime Flow (Manual Mode):**
```
Blynk App Slider Movement (V0-V4)
  → Blynk Cloud
  → ESP32 BLYNK_WRITE handler
  → servo.write(angle)
  → Physical servo movement
```

---

## New Components

### 1. Blynk Setup Tab

**Purpose:** Interactive guide for configuring Blynk mobile app

**UI Layout:**
```
┌─────────────────────────┬──────────────────────────┐
│  📱 App Preview         │  📝 Setup Steps          │
├─────────────────────────┼──────────────────────────┤
│                         │                          │
│  Visual mockup showing: │  Step-by-step checklist: │
│  • 5 slider positions   │  ☐ Add V0 (Base)        │
│  • 1 switch position    │  ☐ Add V1 (Shoulder)    │
│  • Labels               │  ☐ Add V2 (Elbow)       │
│  • Value ranges         │  ☐ Add V3 (Wrist)       │
│                         │  ☐ Add V4 (Gripper)     │
│                         │  ☐ Add V5 (Auto Mode)   │
│                         │                          │
│                         │  [📋 Copy Config]        │
└─────────────────────────┴──────────────────────────┘
```

**Features:**
- **Standard Setup** button (default: 5 sliders + 1 switch)
- **Custom Setup** button (advanced users can modify)
- Copy-paste helpers for widget configuration
- Progress tracking (checkboxes)
- Visual preview updates as student checks items

**Implementation:**
- New HTML section in `frontend/index.html`
- New JavaScript file: `frontend/js/blynk_setup.js`
- CSS styling in `frontend/css/style.css`

---

### 2. Web Serial Flash System

**Purpose:** Flash firmware directly from browser without external tools

**Technology:** Web Serial API (Chrome/Edge only)

**User Flow:**
```
1. Click "Flash via USB" button
2. Browser shows serial port picker
3. Student selects ESP32 COM port
4. IDE uploads firmware with progress bar
5. Serial monitor shows boot messages
6. Success notification when complete
```

**UI Components:**

**Port Selection:**
```
┌─────────────────────────────────────┐
│  🔌 Connect to ESP32                │
├─────────────────────────────────────┤
│  1. Plug ESP32 via USB              │
│  2. Click button below              │
│                                     │
│  [📍 Select Serial Port]            │
│                                     │
│  ⚠️ Chrome/Edge required            │
└─────────────────────────────────────┘
```

**Flashing Progress:**
```
┌─────────────────────────────────────┐
│  ⚡ Flashing ESP32                  │
├─────────────────────────────────────┤
│  ✅ Connected to COM3               │
│  ✅ Detected: ESP32-WROOM-32        │
│  ✅ Erasing flash                   │
│  ⏳ Writing firmware...             │
│                                     │
│  ████████████████░░  85%            │
│  414 KB / 487 KB                    │
│                                     │
│  ⏱️ ~10 seconds remaining           │
└─────────────────────────────────────┘
```

**Success with Serial Monitor:**
```
┌─────────────────────────────────────┐
│  ✅ Flash Complete!                 │
├─────────────────────────────────────┤
│  📡 Serial Monitor:                 │
│  ┌───────────────────────────────┐  │
│  │ WiFi: Connected!              │  │
│  │ IP: 192.168.1.45              │  │
│  │ Blynk: Ready!                 │  │
│  │ Arm controller ready          │  │
│  └───────────────────────────────┘  │
│                                     │
│  ✅ Next: Test in Blynk app        │
│  [Close]                            │
└─────────────────────────────────────┘
```

**Implementation:**
- New JavaScript file: `frontend/js/web_serial.js`
- Uses [esptool-js](https://github.com/espressif/esptool-js) library
- Fallback: "Download .bin" button for unsupported browsers

**Browser Compatibility:**
- ✅ Chrome 89+
- ✅ Edge 89+
- ❌ Firefox (show download option)
- ❌ Safari (show download option)

---

### 3. GPIO Pin Configuration

**Recommended Pin Assignments:**

```cpp
const int PIN_BASE = 25;      // GPIO 25
const int PIN_SHOULDER = 26;  // GPIO 26
const int PIN_ELBOW = 27;     // GPIO 27
const int PIN_WRIST = 32;     // GPIO 32
const int PIN_GRIPPER = 33;   // GPIO 33
```

**Why These Pins?**

**Safe for servo PWM:**
- GPIO 25-27: ADC2 pins, safe for output
- GPIO 32-33: ADC1 pins, safe for output
- All support LEDC PWM for servo control

**Avoid:**
- GPIO 0, 2, 5, 12, 15: Boot mode pins
- GPIO 34-39: Input-only
- GPIO 6-11: Connected to flash
- GPIO 1, 3: Serial TX/RX

**Configuration Approach:**
- Phase 1: Hardcoded in firmware template
- Phase 2 (future): Allow customization in IDE

**Wiring Diagram:**
```
ESP32              Servo (×5)
┌───────┐          
│  GND  ├──────────── Brown (GND)
│ GPIO25├──────────── Orange (Signal)
└───────┘            Red (5V) ──┐
                                │
         External 5V Supply ────┘
         (2A minimum, shared GND)
```

---

### 4. Build System Enhancements

**Current State:**
- Template engine fills placeholders
- arduino-cli compiles firmware
- Returns .bin file

**Changes for Manual Mode:**

**New Build Button:**
```
[🔨 Build for Manual Mode]
Build firmware to test hardware
```

**What Gets Compiled:**
- WiFi credentials (from Setup tab)
- Blynk configuration (from Setup tab)
- GPIO pins (hardcoded: 25, 26, 27, 32, 33)
- Manual control handlers (BLYNK_WRITE V0-V5)
- **Empty** `runStudentProgram()` function

**Build Process:**
```python
def build_manual_mode_firmware(settings: dict) -> str:
    """Generate manual control firmware."""
    template = read_file("backend/templates/arm_controller.ino")
    
    # Fill placeholders
    firmware = template.replace("{{WIFI_SSID}}", settings["wifi_ssid"])
    firmware = firmware.replace("{{WIFI_PASSWORD}}", settings["wifi_password"])
    firmware = firmware.replace("{{BLYNK_TEMPLATE_ID}}", settings["blynk_template_id"])
    firmware = firmware.replace("{{BLYNK_AUTH_TOKEN}}", settings["blynk_auth_token"])
    firmware = firmware.replace("{{POSE_DEFINITIONS}}", "")  # Empty for manual mode
    firmware = firmware.replace("{{GENERATED_CODE}}", "// Manual mode only")
    
    # Compile with arduino-cli
    return compile_arduino(firmware)
```

**Validation Before Build:**
- All required settings present
- WiFi SSID not empty
- Blynk auth token format valid (TMPL...)

---

### 5. Testing & Validation System

**Post-Flash Checklist UI:**
```
┌─────────────────────────────────────┐
│  ✅ Firmware Flashed Successfully   │
├─────────────────────────────────────┤
│  Now let's test your hardware:      │
│                                     │
│  Manual Control Checklist:          │
│  ☐ ESP32 shows online in Blynk     │
│  ☐ Base servo responds (V0)        │
│  ☐ Shoulder servo responds (V1)    │
│  ☐ Elbow servo responds (V2)       │
│  ☐ Wrist servo responds (V3)       │
│  ☐ Gripper servo responds (V4)     │
│  ☐ Auto Mode switch visible (V5)   │
│                                     │
│  [✓ All Working]  [📝 Report Issue]│
└─────────────────────────────────────┘
```

**Troubleshooting Helper:**

If student reports issue, show diagnostic wizard:
```
What's not working?
○ ESP32 won't connect to WiFi
○ Blynk shows "offline"
○ One servo doesn't move
○ All servos don't move
○ Other issue
```

**Example diagnostic (servo doesn't move):**
```
┌─────────────────────────────────────┐
│  🔧 Servo Not Moving                │
├─────────────────────────────────────┤
│  Common causes:                     │
│                                     │
│  1. ⚡ Power supply                 │
│     • Servos need external 5-6V    │
│     • Check connections            │
│     • Verify shared ground         │
│                                     │
│  2. 🔌 Wiring                       │
│     • Check GPIO pin number        │
│     • Verify signal wire           │
│                                     │
│  [📖 View Wiring Guide]            │
└─────────────────────────────────────┘
```

---

### 6. Help & Documentation System

**Context-Sensitive Help:**

Each tab has a help icon (❓) showing relevant guidance:

**Setup Tab:**
```
ℹ️ WiFi & Blynk Configuration

WiFi:
• ESP32 requires 2.4GHz WiFi (not 5GHz)
• No enterprise/WPA2-Enterprise support

Blynk:
• Get credentials from blynk.cloud
• Create device template
• Generate auth token

[📹 Video Tutorial] [📖 Detailed Guide]
```

**Blynk Setup Tab:**
```
ℹ️ Configuring Blynk Mobile App

Widgets:
• Sliders (V0-V4): Control servo angles
• Switch (V5): Toggle auto/manual mode

Manual Mode:
• Auto Mode OFF = sliders control servos
• Use for testing and teaching poses

[📹 Watch Setup Video]
```

**Wiring Diagram:**

Accessible from multiple locations:
```
┌─────────────────────────────────────┐
│  🔌 ESP32 → Servo Wiring            │
├─────────────────────────────────────┤
│  [Diagram showing connections]      │
│                                     │
│  Pin Assignments:                   │
│  • GPIO 25 → Base                   │
│  • GPIO 26 → Shoulder               │
│  • GPIO 27 → Elbow                  │
│  • GPIO 32 → Wrist                  │
│  • GPIO 33 → Gripper                │
│                                     │
│  ⚠️ Servos need external 5V supply  │
│                                     │
│  [📥 Download PDF] [🖨️ Print]      │
└─────────────────────────────────────┘
```

---

## Error Handling

### Error Categories

**1. Configuration Errors (Preventable)**
- Missing WiFi credentials → Disable build, show warning
- Invalid Blynk token → Validate on save
- Empty required fields → Form validation

**2. Build Errors (Recoverable)**
- arduino-cli not found → Installation guide with links
- Compilation failed → Show error log with context
- Library missing → Installation command

**3. Flash Errors (Recoverable)**
- USB permission denied → Instructions + retry
- Wrong COM port → Show port picker again
- Flash timeout → Reset instructions

**4. Runtime Errors (Requires debugging)**
- WiFi connection fails → Check credentials
- Blynk offline → Verify token, internet
- Servo not moving → Hardware guide

### Error UI Pattern

Consistent format across all error types:
```
┌─────────────────────────────────────┐
│  ❌ [Error Category]                │
├─────────────────────────────────────┤
│  What happened:                     │
│  [Clear, jargon-free description]   │
│                                     │
│  How to fix:                        │
│  1. [Actionable step 1]             │
│  2. [Actionable step 2]             │
│  3. [Actionable step 3]             │
│                                     │
│  [🔄 Try Again]  [📖 More Help]    │
└─────────────────────────────────────┘
```

### Recovery Actions

- **Auto-save:** Settings save automatically on change
- **Build retry:** Previous settings retained
- **Flash retry:** Can re-flash same .bin without rebuild
- **State preservation:** IDE remembers progress on page reload

---

## File Structure

### Project Files
```
projects/
  └── default/
      ├── settings.json         # WiFi + Blynk config
      ├── poses.json            # Saved poses (not used yet)
      └── workspace.xml         # Blockly workspace (not used yet)
```

### Build Artifacts
```
builds/
  └── {uuid}/
      ├── sketch/
      │   └── sketch.ino       # Generated firmware
      └── sketch.ino.bin       # Compiled binary
```

### Templates
```
backend/templates/
  ├── arm_controller.ino       # Main template (manual mode)
  └── vision_board.ino         # ESP32-CAM (not used in Phase 1)
```

### Settings Format
```json
{
  "wifi_ssid": "MyHomeWiFi",
  "wifi_password": "password123",
  "blynk_template_id": "TMPL1234567890",
  "blynk_template_name": "Robot Controller",
  "blynk_auth_token": "abc123xyz789def456"
}
```

---

## Implementation Plan

### New Files

**Frontend:**
- `frontend/js/blynk_setup.js` - New tab logic
- `frontend/js/web_serial.js` - USB flashing
- `frontend/css/blynk_setup.css` - Tab styling

**Backend:**
- `backend/routes/flash.py` - Flash endpoint (if needed)

**Documentation:**
- `docs/BLYNK_SETUP_GUIDE.md` - Printable guide
- `docs/WIRING_DIAGRAM.pdf` - Visual reference

### Modified Files

**Frontend:**
- `frontend/index.html` - Add Blynk Setup tab
- `frontend/css/style.css` - Update tab styling
- `frontend/js/main.js` - Tab switching logic

**Backend:**
- `backend/templates/arm_controller.ino` - Update GPIO pins to 25-33

### Dependencies

**New npm packages (frontend):**
```json
{
  "esptool-js": "^1.0.0"  // Web Serial flashing
}
```

**Existing packages (no changes):**
- FastAPI
- uvicorn
- arduino-cli (external tool)

---

## Testing Strategy

### Unit Tests (Backend)

```python
# test_template_engine.py
def test_fill_manual_mode_template():
    settings = load_test_settings()
    firmware = fill_template(settings, poses={}, code="")
    assert "MyHomeWiFi" in firmware
    assert "GPIO 25" in firmware

# test_build.py
def test_build_manual_mode():
    result = build_manual_mode_firmware(test_settings)
    assert result.success
    assert result.firmware_size > 0
```

### Integration Tests

```python
# test_full_flow.py
def test_complete_manual_mode_flow():
    # Save settings
    response = client.post("/api/settings", json=test_settings)
    assert response.status_code == 200
    
    # Build firmware
    response = client.post("/api/build", json={"mode": "manual"})
    assert response.status_code == 200
    assert "firmware.bin" in response.json()
```

### Manual Testing Checklist

**Frontend:**
- [ ] All 4 tabs load correctly
- [ ] Setup form validates inputs
- [ ] Settings persist after page reload
- [ ] Blynk setup guide displays mockup
- [ ] Build modal shows progress
- [ ] Error messages are clear

**Backend:**
- [ ] Settings API saves/loads correctly
- [ ] Template engine fills all placeholders
- [ ] arduino-cli compiles successfully
- [ ] .bin file is downloadable

**Hardware (with physical ESP32):**
- [ ] Web Serial connects to ESP32
- [ ] Firmware flashes without errors
- [ ] ESP32 connects to WiFi
- [ ] ESP32 shows online in Blynk
- [ ] All 5 servos respond to sliders
- [ ] Auto mode toggle visible (stays OFF)

**End-to-End:**
- [ ] New student can complete full workflow in 30 minutes
- [ ] Error recovery works (retry flash, rebuild, etc.)
- [ ] Help documentation is accessible and clear

---

## Success Criteria

### Phase 1 Complete When:

1. ✅ Student can configure IDE with WiFi + Blynk credentials
2. ✅ Student can build firmware from IDE
3. ✅ Student can flash ESP32 via USB (Web Serial)
4. ✅ ESP32 connects to WiFi and Blynk automatically
5. ✅ All 5 servos respond to Blynk app sliders
6. ✅ Student can validate hardware working correctly
7. ✅ Clear error messages guide debugging

### Metrics:

- **Setup time:** < 30 minutes for new student (first flash)
- **Build time:** < 60 seconds (arduino-cli)
- **Flash time:** < 90 seconds (Web Serial)
- **Success rate:** > 95% (with proper hardware setup)

---

## Future Enhancements (Phase 2)

**Not included in this design:**

1. **Automatic Mode:**
   - Execute block programs in `runStudentProgram()`
   - Auto mode toggle switch activates program loop

2. **Teach Poses Integration:**
   - Save poses from manual control
   - Use poses in block programs

3. **OTA Updates:**
   - Wireless firmware updates after first flash
   - No USB cable needed for iterations

4. **Advanced Features:**
   - Camera/vision integration
   - Custom GPIO pin configuration
   - Firmware rollback
   - Real-time debugging

---

## Security Considerations

**Web Serial API:**
- Requires user consent (browser permission)
- Only works with physical USB connection
- Cannot access arbitrary serial ports

**Credentials Storage:**
- WiFi passwords stored in plain text in `settings.json`
- **Risk:** Local file access = credentials exposed
- **Mitigation:** Warn users not to commit settings.json
- **Future:** Encrypt sensitive fields

**Blynk Token:**
- Auth token gives full device control
- **Risk:** Token in settings.json = device access
- **Mitigation:** Use device-specific tokens, not account tokens
- **Future:** Token masking in UI

**arduino-cli:**
- Executes shell commands with user input
- **Risk:** Command injection via settings
- **Mitigation:** Validate and sanitize all inputs
- **Implementation:** Use parameterized commands, not string concatenation

---

## Accessibility

**Keyboard Navigation:**
- All tabs accessible via Tab key
- Build button: Space or Enter
- Modal dialogs: Esc to close

**Screen Reader Support:**
- ARIA labels on all interactive elements
- Status announcements for build progress
- Error messages marked as alerts

**Visual:**
- Color not sole indicator (use icons + text)
- High contrast mode compatible
- Font size adjustable (browser zoom)

---

## Appendix A: Blynk Widget Configuration

### Standard Setup Details

**Slider Widgets (V0-V4):**
```
Widget Type: Slider
Pin: V0 (Base), V1 (Shoulder), V2 (Elbow), V3 (Wrist), V4 (Gripper)
Data Type: Integer
Min Value: 0
Max Value: 180
Step: 1
Send on release: OFF (continuous updates)
```

**Switch Widget (V5):**
```
Widget Type: Switch
Pin: V5
Data Type: Integer
Values: 0 (OFF) / 1 (ON)
Label: "Auto Mode"
Default: OFF
```

---

## Appendix B: ESP32 Boot Messages

**Expected Serial Output After Flash:**
```
rst:0x1 (POWERON_RESET),boot:0x13 (SPI_FAST_FLASH_BOOT)
configsip: 0, SPIWP:0xee
clk_drv:0x00,q_drv:0x00,d_drv:0x00,cs0_drv:0x00,hd_drv:0x00,wp_drv:0x00
mode:DIO, clock div:2
load:0x3fff0030,len:1344
load:0x40078000,len:13964
load:0x40080400,len:3600
entry 0x400805f0

WiFi: Connecting to MyHomeWiFi...
WiFi: Connected!
IP Address: 192.168.1.45

Blynk: Connecting...
[1234] Blynk v1.2.0
[1456] Using auth token: abc...
Blynk: Connected!

Arm controller ready
```

**Troubleshooting Common Boot Errors:**
- `rst:0x10 (RTCWDT_RTC_RESET)` → Power supply issue
- `WiFi: Connection failed` → Wrong SSID/password
- `Blynk: Connection timeout` → Invalid auth token or no internet

---

## Appendix C: arduino-cli Commands

**Installation:**
```bash
# Windows
choco install arduino-cli

# macOS
brew install arduino-cli

# Linux
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```

**Setup ESP32:**
```bash
arduino-cli config init
arduino-cli core update-index
arduino-cli core install esp32:esp32
arduino-cli lib install "Blynk"
arduino-cli lib install "ESP32Servo"
```

**Compile Command Used by IDE:**
```bash
arduino-cli compile \
  --fqbn esp32:esp32:esp32 \
  --output-dir ./builds/{uuid} \
  ./builds/{uuid}/sketch
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-06-03 | Claude | Initial design approved |

---

**End of Design Document**
