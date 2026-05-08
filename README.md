# Block Coding Robot IDE

A web-based block-coding IDE for programming ESP32-based robotic systems with computer vision support.

## Project Overview

**DLSU Thesis Project:** RIAL-3-2425-C7  
**Title:** Development of a Cost-Effective 3D-Printed Pick-and-Place Robotic Arm for Object Sorting and Educational Applications

This IDE allows students to program a 5-DOF robotic arm using Scratch-style blocks instead of text-based coding. The system includes:
- **Drag-and-drop block editor** (powered by Blockly)
- **Automatic C++ code generation** for ESP32 firmware
- **Built-in computer vision** support via ESP32-CAM
- **Mobile control** via Blynk app
- **Pose teaching** interface for recording robot positions

## Quick Start

### Prerequisites

- Python 3.8 or higher
- arduino-cli (see [setup guide](docs/ARDUINO_CLI_SETUP.md))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd block-coding-robot
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up arduino-cli** (optional for UI testing)
   Follow the instructions in [docs/ARDUINO_CLI_SETUP.md](docs/ARDUINO_CLI_SETUP.md)

### Running the IDE

1. **Start the backend server**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

2. **Open in browser**
   Navigate to [http://localhost:8000](http://localhost:8000)

---

## Testing the IDE

### Quick Test (No Hardware/arduino-cli Needed)

1. **Start the server:**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

2. **Open browser:** http://localhost:8000

3. **Test each workspace:**

   **📋 Setup Tab:**
   - Fill in WiFi credentials (use test values like `TestNetwork` / `password123`)
   - Add Blynk settings: Template ID: `TMPL123`, Name: `Test Robot`, Token: `token123`
   - Click **"💾 Save Settings"** → green success message appears
   - Click **"🔄 Reload"** to verify settings persist

   **🎯 Teach Poses Tab:**
   - Drag servo sliders (Base, Shoulder, Elbow, Wrist, Gripper)
   - Set angles: Base=45°, Shoulder=60°, Elbow=90°, Wrist=120°, Gripper=30°
   - Click **"💾 Save Current Pose"** → name it `PICKUP`
   - See pose card appear with angles `[45, 60, 90, 120, 30]`
   - Create another pose named `DROP_ZONE`
   - Try deleting a custom pose (HOME cannot be deleted)

   **📦 Program Tab:**
   - Left panel has Blockly editor with colored toolbox
   - Right panel shows live C++ code preview
   - Drag blocks from toolbox:
     - **Arm Control** (blue): move to pose, open/close claw, wait
     - **Vision** (purple): camera sees, detection, confidence
     - **Logic** (green): forever, if/else, repeat, wait
   - Create a simple program:
     ```
     forever
       if camera sees "red_small" > 70%
         move arm to pose PICKUP
         close claw
         wait 1 seconds
         move arm to pose DROP_ZONE
         open claw
     ```
   - Watch code preview update in real-time
   - Status bar shows block count

4. **Test Build Button (UI only):**
   - Click **"🔨 Build & Flash"** button in header
   - Modal dialog appears with spinner
   - Without arduino-cli: "arduino-cli not found" error (expected)
   - With arduino-cli: compilation runs, .bin download on success

### Full Test (With arduino-cli Installed)

1. Follow [docs/ARDUINO_CLI_SETUP.md](docs/ARDUINO_CLI_SETUP.md) to install arduino-cli
2. Create blocks in Program tab
3. Click "Build & Flash"
4. Wait 30-60 seconds for compilation
5. Download .bin file
6. Flash to ESP32: [docs/FLASH_INSTRUCTIONS.md](docs/FLASH_INSTRUCTIONS.md)

### API Testing (Backend)

Test endpoints directly with curl:

```bash
# Health check
curl http://localhost:8000/health

# Get settings
curl http://localhost:8000/api/settings

# Save settings
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"wifi_ssid":"test","wifi_password":"test","blynk_template_id":"TMPL123","blynk_template_name":"Test","blynk_auth_token":"token"}'

# Get poses
curl http://localhost:8000/api/poses

# Save a pose
curl -X POST http://localhost:8000/api/poses \
  -H "Content-Type: application/json" \
  -d '{"name":"TEST_POSE","angles":[45,60,90,120,30]}'

# Delete a pose
curl -X DELETE http://localhost:8000/api/poses/TEST_POSE
```

### Expected Results

✅ **What Works:**
- Professional IDE interface loads instantly
- Three workspaces switch smoothly (Setup, Program, Poses)
- Settings save to `projects/default/settings.json`
- Poses save to `projects/default/poses.json`
- Saved poses appear in block dropdowns immediately
- Blocks snap together and generate Arduino C++ code
- Code preview updates in real-time as blocks change
- Build system triggers arduino-cli compilation
- Download .bin firmware file on successful build
- Status bar shows live counts (blocks, poses)

❌ **Known Limitations:**
- Build fails gracefully without arduino-cli (shows helpful error)
- No actual robot control yet (needs physical hardware + Blynk setup)
- Vision uses mock inference placeholder (real TFLite model needed in week 1)
- GPIO pins are placeholders until hardware testing

---

## Project Structure

```
block-coding-robot/
├── backend/                    # FastAPI backend
│   ├── main.py                 # Entry point
│   ├── routes/                 # API endpoints (build, settings, poses)
│   ├── services/               # Business logic (builder, storage, template engine)
│   └── templates/              # Firmware templates (.ino files)
├── frontend/                   # Static web interface
│   ├── index.html              # Main IDE shell
│   ├── css/                    # Stylesheets
│   └── js/                     # JavaScript modules
│       ├── blocks/             # Blockly block definitions
│       ├── generators/         # Arduino C++ code generator
│       └── ui/                 # UI components (setup, poses, build)
├── docs/                       # Documentation
├── projects/                   # User project storage (gitignored)
└── builds/                     # Compiled binaries (gitignored)
```

## Hardware Setup

### Components
- ESP32 Dev Module (arm controller)
- ESP32-CAM (vision board)
- 5 servo motors (base, shoulder, elbow, wrist, gripper)
- External power supply for servos

### Pin Assignments
See [docs/HARDWARE_PINOUT.md](docs/HARDWARE_PINOUT.md) for GPIO pin mappings (to be documented during hardware testing).

## Development Status

- [x] Project scaffold & directory structure
- [x] FastAPI backend with 3 API routers
- [x] Frontend interface with 3 workspaces
- [x] Firmware templates (arm controller + vision board)
- [x] Backend services (builder, storage, template engine)
- [x] Blockly integration with custom blocks
- [x] Block library (arm, vision, logic, math, variables)
- [x] Pose teaching interface
- [x] Build pipeline (arduino-cli wrapper)
- [x] Code generator (Blocks → Arduino C++)
- [x] **LEGO Object Detection Training Pipeline** (NEW)
  - [x] Complete training scripts (8 files)
  - [x] Comprehensive documentation (6 guides)
  - [x] 20+ automatic visualizations
  - [x] Google Colab support (GPU training)
- [ ] arduino-cli installation
- [ ] Hardware integration & GPIO pin documentation
- [ ] TFLite model integration for real vision
- [ ] End-to-end robot testing

## Features

### ✅ Implemented
- Visual block programming with Blockly
- Real-time code preview (Arduino C++)
- WiFi & Blynk configuration UI
- Pose teaching & management
- Firmware compilation via arduino-cli
- Binary download for ESP32
- REST API for settings/poses/build
- Responsive web interface
- Error handling & status feedback

### 🔄 Planned (Week 1+)
- TFLite Micro model integration
- Hardware GPIO pin mapping
- Real robot testing with servos
- Vision board firmware with actual inference
- Blynk mobile app dashboard design

## Documentation

- [Arduino CLI Setup Guide](docs/ARDUINO_CLI_SETUP.md) - Install and configure arduino-cli + ESP32 core
- [Flash Instructions](docs/FLASH_INSTRUCTIONS.md) - How to flash .bin files to ESP32 boards
- [Hardware Pinout](docs/HARDWARE_PINOUT.md) - GPIO pin assignments (TBD)
- [TESTING.md](TESTING.md) - Detailed testing guide and checklists

## Troubleshooting

**IDE won't load:**
- Check server is running: `curl http://localhost:8000/health`
- Check browser console (F12) for JavaScript errors
- Try hard refresh: Ctrl+F5

**Build fails:**
- Install arduino-cli: see [docs/ARDUINO_CLI_SETUP.md](docs/ARDUINO_CLI_SETUP.md)
- Configure settings in Setup tab first
- Add at least one block before building

**Blocks don't generate code:**
- Check browser console for errors
- Verify Blockly loaded from CDN (needs internet)
- Try refreshing the page

## Contributing

This is a thesis project with a fixed scope for academic requirements. External contributions are not being accepted at this time.

## License

Academic use only - DLSU Thesis Project

## Contact

For questions about this thesis project, contact the DLSU RIAL-3-2425-C7 team.

---

**Server Running?** Check status: http://localhost:8000/health  
**Need Help?** See [TESTING.md](TESTING.md) for detailed testing guide.
