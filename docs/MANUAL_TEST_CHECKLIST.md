# Manual Test Checklist - Hardware Integration Phase 1

Complete checklist for testing manual control integration.

---

## Pre-Testing Setup

- [ ] ESP32 board available and powered
- [ ] 5 servos connected to GPIO 25, 26, 27, 32, 33
- [ ] External 5V power supply (2A+) connected to servos
- [ ] Ground shared between ESP32 and power supply
- [ ] USB cable for flashing
- [ ] WiFi network available (2.4GHz)
- [ ] Blynk account created with device template
- [ ] Blynk mobile app installed on phone

---

## Frontend Tests

### Tab Structure
- [ ] 1. IDE loads at http://localhost:8000
- [ ] 2. Four tabs visible: Setup, Blynk Setup, Teach Poses, Program
- [ ] 3. Click each tab - workspace switches correctly
- [ ] 4. No console errors in browser dev tools

### Setup Tab
- [ ] 5. Form has WiFi SSID field
- [ ] 6. Form has WiFi Password field
- [ ] 7. Form has Blynk Template ID field
- [ ] 8. Form has Blynk Auth Token field
- [ ] 9. Fill in test credentials and save
- [ ] 10. Green success message appears
- [ ] 11. Reload page - settings persist

### Blynk Setup Tab
- [ ] 12. Click "📱 Blynk Setup" tab
- [ ] 13. Two buttons visible: Standard Setup, Custom Setup
- [ ] 14. Click "Standard Setup"
- [ ] 15. Left panel shows app mockup with sliders
- [ ] 16. Right panel shows widget checklist
- [ ] 17. Check one item - checkbox works
- [ ] 18. Click copy button - text copies to clipboard
- [ ] 19. Copy button shows "✓ Copied" feedback
- [ ] 20. Click "Custom Setup" - shows "coming soon" message

---

## Build System Tests

### Build Process
- [ ] 21. Click "🔨 Build for Manual Mode" (if button exists)
- [ ] 22. Build modal appears
- [ ] 23. Progress indicator shows
- [ ] 24. Build completes successfully
- [ ] 25. Firmware size displayed (e.g., "487 KB")

### Flash Options
- [ ] 26. "Flash via USB" button visible
- [ ] 27. "Download .bin" button visible
- [ ] 28. If Firefox/Safari: warning about browser compatibility shows
- [ ] 29. If Chrome/Edge: no warning (Web Serial supported)

---

## Flash System Tests (Chrome/Edge Only)

### USB Flash
- [ ] 30. Plug in ESP32 via USB
- [ ] 31. Click "Flash via USB"
- [ ] 32. Browser permission dialog appears
- [ ] 33. Select ESP32 serial port (e.g., COM3)
- [ ] 34. Flash modal appears
- [ ] 35. Step 1: "Serial port selected" ✅
- [ ] 36. Step 2: "Connected to ESP32" ✅
- [ ] 37. Step 3: "Firmware downloaded" ✅
- [ ] 38. Step 4: Progress bar animates
- [ ] 39. Step 5: "Firmware flashed successfully" ✅
- [ ] 40. Validation checklist appears

### Validation Checklist
- [ ] 41. Checklist has 7 items
- [ ] 42. Can check/uncheck items
- [ ] 43. "✓ All Working" button visible
- [ ] 44. "📝 Report Issue" button visible
- [ ] 45. Click "Report Issue" - troubleshooting modal opens
- [ ] 46. Troubleshooting has 5 issue options
- [ ] 47. Click an option - advice appears
- [ ] 48. Advice is specific and helpful

---

## Hardware Tests (Physical ESP32)

### ESP32 Boot
- [ ] 49. ESP32 reboots after flash
- [ ] 50. Serial monitor shows boot messages
- [ ] 51. Serial monitor shows "WiFi: Connected!"
- [ ] 52. Serial monitor shows "Blynk: Connected!"
- [ ] 53. Serial monitor shows "Arm controller ready"

### Blynk App Connection
- [ ] 54. Open Blynk app on phone
- [ ] 55. Device shows "Online" (green)
- [ ] 56. All 6 widgets visible (5 sliders + 1 switch)
- [ ] 57. Widgets have correct labels (Base, Shoulder, etc.)

### Manual Control - Base Servo
- [ ] 58. Ensure "Auto Mode" switch is OFF
- [ ] 59. Move "Base" slider to 0°
- [ ] 60. Servo moves to minimum position
- [ ] 61. Move slider to 180°
- [ ] 62. Servo moves to maximum position
- [ ] 63. Move slider to 90°
- [ ] 64. Servo centers

### Manual Control - Shoulder Servo
- [ ] 65. Move "Shoulder" slider through range
- [ ] 66. Correct servo responds (not Base)
- [ ] 67. Servo moves smoothly

### Manual Control - Elbow Servo
- [ ] 68. Move "Elbow" slider through range
- [ ] 69. Correct servo responds
- [ ] 70. Servo moves smoothly

### Manual Control - Wrist Servo
- [ ] 71. Move "Wrist" slider through range
- [ ] 72. Correct servo responds
- [ ] 73. Servo moves smoothly

### Manual Control - Gripper Servo
- [ ] 74. Move "Gripper" slider to 30° (open)
- [ ] 75. Gripper opens
- [ ] 76. Move slider to 90° (closed)
- [ ] 77. Gripper closes

### Auto Mode Toggle
- [ ] 78. "Auto Mode" switch visible
- [ ] 79. Switch defaults to OFF
- [ ] 80. Toggle to ON (for future use)
- [ ] 81. Toggle back to OFF

---

## Documentation Tests

- [ ] 82. `docs/BLYNK_SETUP_GUIDE.md` exists and is complete
- [ ] 83. Guide has step-by-step widget instructions
- [ ] 84. Guide has troubleshooting section
- [ ] 85. Guide has quick reference card
- [ ] 86. `docs/HARDWARE_PINOUT.md` documents GPIO pins 25-33
- [ ] 87. All documentation links work

---

## Error Handling Tests

### Missing Settings
- [ ] 88. Click build with empty WiFi SSID
- [ ] 89. Error message appears
- [ ] 90. Build is prevented

### USB Permission Denied
- [ ] 91. Click "Flash via USB"
- [ ] 92. Deny browser permission
- [ ] 93. Error message shown
- [ ] 94. "Try Again" button available

### Troubleshooting Flow
- [ ] 95. Simulate issue (e.g., wrong WiFi password)
- [ ] 96. Flash firmware
- [ ] 97. ESP32 fails to connect
- [ ] 98. Click "Report Issue" in validation
- [ ] 99. Select "ESP32 won't connect to WiFi"
- [ ] 100. Relevant advice displayed

---

## Performance Tests

- [ ] 101. Page load time < 2 seconds
- [ ] 102. Tab switching is instant
- [ ] 103. Build time < 60 seconds (if arduino-cli installed)
- [ ] 104. Flash time < 90 seconds
- [ ] 105. Servo response is immediate (no lag)

---

## Cross-Browser Tests

### Chrome
- [ ] 106. All features work
- [ ] 107. Web Serial flash works
- [ ] 108. No console errors

### Edge
- [ ] 109. All features work
- [ ] 110. Web Serial flash works

### Firefox
- [ ] 111. IDE loads correctly
- [ ] 112. Web Serial warning shows
- [ ] 113. Download .bin works as fallback

---

## Regression Tests (Existing Features)

- [ ] 114. Teach Poses tab still works
- [ ] 115. Program tab still works
- [ ] 116. Existing build system unaffected
- [ ] 117. Settings API still works

---

## AP Mode Tests

### Basic Connectivity
- [ ] ESP32 boots and creates WiFi AP (check serial monitor)
- [ ] SSID format is RobotArm-XXXX (X = hex digits from MAC)
- [ ] Phone can see and connect to robot WiFi
- [ ] Password "robot1234" works
- [ ] Captive portal opens automatically (iOS and Android)
- [ ] PWA loads at 192.168.4.1
- [ ] Connection status shows "Connected" (green dot)

### WebSocket Communication
- [ ] WebSocket connects (check browser console)
- [ ] Initial state received (servos sync to current positions)
- [ ] Moving slider sends servo command
- [ ] Servo moves in real-time (<100ms)
- [ ] Value display updates (0°-180°)
- [ ] Mode toggle sends mode command
- [ ] Reset button sends reset command

### Multi-Client Test
- [ ] Connect 2 phones simultaneously
- [ ] Both show "Connected" status
- [ ] Move slider on Phone A → servo moves, both phones update
- [ ] Move slider on Phone B → servo moves, both phones update
- [ ] Disconnect Phone A → Phone B still works
- [ ] Reconnect Phone A → syncs current state

### Manual Control Test
- [ ] All 5 sliders control correct servos:
  - [ ] Base slider → base servo rotates
  - [ ] Shoulder slider → shoulder joint moves
  - [ ] Elbow slider → elbow joint moves
  - [ ] Wrist slider → wrist rotates
  - [ ] Gripper slider → gripper opens/closes
- [ ] Servo positions match slider values
- [ ] No jitter or unexpected movements
- [ ] Smooth motion (no lag)

### Auto Mode Test
- [ ] Toggle "Auto" mode → mode indicator changes
- [ ] Student program runs (servos execute sequence)
- [ ] Manual sliders disabled during auto mode
- [ ] Toggle back to "Manual" → regain control
- [ ] Reset button works in manual mode

### PWA Features Test
- [ ] "Add to Home Screen" works (iOS and Android)
- [ ] App icon appears on home screen
- [ ] Opening from home screen shows full screen (no browser bar)
- [ ] Service worker caches files (check browser DevTools)
- [ ] Offline page loads if connection lost

### Error Handling Test
- [ ] Disconnect WiFi → status shows "Disconnected"
- [ ] Controls grey out when disconnected
- [ ] Auto-reconnect works (rejoin WiFi)
- [ ] State syncs on reconnection
- [ ] Invalid JSON ignored (check serial monitor)

### Range Test
- [ ] Connection works at 1 meter
- [ ] Connection works at 10 meters
- [ ] Connection works at 20 meters
- [ ] Note max reliable range: _____ meters

### Interference Test (Classroom Simulation)
- [ ] 3+ robots powered on nearby
- [ ] Each has unique SSID
- [ ] Can connect to specific robot
- [ ] No cross-talk between robots
- [ ] Performance acceptable with neighbors

## Regression Tests (Ensure Nothing Broke)

### Build System
- [ ] Desktop IDE still loads
- [ ] Setup tab shows AP mode instructions
- [ ] Build & Flash button works
- [ ] Compilation succeeds
- [ ] USB flashing works
- [ ] Binary size reasonable (<1MB)

### Servo Control (PCA9685)
- [ ] I2C communication works
- [ ] All 5 servos respond
- [ ] Angle mapping correct (0-180°)
- [ ] Default positions: Base=0, Shoulder=60, Elbow=70, Wrist=60, Gripper=90
- [ ] No change from previous firmware behavior

### Block Programming
- [ ] Blockly workspace loads
- [ ] Can create block programs
- [ ] Code generation works
- [ ] Pose definitions included in build
- [ ] Generated code compiles

## Test Environment

- [ ] **ESP32 Model:** ___________________________
- [ ] **Phone Model (iOS):** ___________________________
- [ ] **Phone Model (Android):** ___________________________
- [ ] **Laptop OS:** ___________________________
- [ ] **Browser (Desktop):** ___________________________
- [ ] **Browser (Mobile):** ___________________________
- [ ] **WiFi Environment:** Home / Classroom / Other: _____
- [ ] **Number of nearby APs:** _____
- [ ] **Test Date:** ___________________________
- [ ] **Tester Name:** ___________________________

## Issues Found

| # | Issue Description | Severity | Status | Notes |
|---|-------------------|----------|--------|-------|
| 1 |                   |          |        |       |
| 2 |                   |          |        |       |
| 3 |                   |          |        |       |

---

## Success Criteria

**Phase 1 Complete When:**
- All 117 checklist items pass ✅
- No critical bugs found
- Documentation is complete and accurate
- Student can complete workflow in < 30 minutes

---

**Testing Date:** ___________  
**Tester Name:** ___________  
**Hardware Setup:** ___________  
**Notes:**
