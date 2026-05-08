# Testing Guide for Block Robot IDE

## Quick Start

1. **Start the server** (if not already running):
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

2. **Open in browser:**
   ```
   http://localhost:8000
   ```

---

## Test Checklist

### ✅ Setup Workspace

- [ ] Fill in WiFi SSID and password
- [ ] Fill in Blynk credentials (dummy values OK for testing)
- [ ] Click "Save Settings" - green success message appears
- [ ] Click "Reload" - settings persist
- [ ] Check file created: `projects/default/settings.json`

### ✅ Pose Teaching Workspace

- [ ] Drag all 5 servo sliders - angles update in real-time
- [ ] Click "Save Current Pose" - prompt appears
- [ ] Enter pose name (e.g., "PICKUP") - pose card appears
- [ ] Create multiple poses - all appear in grid
- [ ] Delete a custom pose - it disappears (HOME cannot be deleted)
- [ ] Status bar shows correct pose count

### ✅ Program Workspace

- [ ] Blockly editor loads with colored toolbox
- [ ] Drag "move arm to pose" block - dropdown shows your saved poses
- [ ] Drag "close claw" and "open claw" blocks - they snap together
- [ ] Drag "wait X seconds" block - number is editable
- [ ] Drag "camera sees" block - dropdown has object classes
- [ ] Drag "forever" block - can nest other blocks inside
- [ ] Drag "if" block from Logic category - conditional logic works
- [ ] Code preview updates automatically on right side
- [ ] Status bar shows correct block count
- [ ] Delete blocks by dragging to trash can

### ✅ Build System

**Without arduino-cli (expected to fail gracefully):**
- [ ] Add blocks to workspace
- [ ] Click "Build & Flash" button
- [ ] Modal dialog appears with spinner
- [ ] Error message: "arduino-cli not found..."
- [ ] Error includes helpful troubleshooting tips
- [ ] Close modal with X button or click outside

**With arduino-cli installed:**
- [ ] Add simple blocks (e.g., move to HOME, wait 1 second)
- [ ] Click "Build & Flash"
- [ ] Compilation succeeds (may take 30-60 seconds)
- [ ] Build log appears in modal
- [ ] Download button appears
- [ ] Click download - .bin file downloads
- [ ] File size is reasonable (~1MB for ESP32)

### ✅ User Interface

- [ ] Tab switching works smoothly (Setup → Program → Poses)
- [ ] All buttons have hover effects
- [ ] Forms validate input (try empty fields)
- [ ] Status bar updates in real-time
- [ ] Code preview has syntax highlighting (dark theme)
- [ ] Responsive design (try resizing window)
- [ ] No console errors (press F12 to check)

### ✅ API Endpoints (curl tests)

```bash
# Get settings
curl http://localhost:8000/api/settings

# Save settings (POST)
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"wifi_ssid":"test","wifi_password":"test","blynk_template_id":"TMPL123","blynk_template_name":"Test","blynk_auth_token":"token123"}'

# Get poses
curl http://localhost:8000/api/poses

# Add pose (POST)
curl -X POST http://localhost:8000/api/poses \
  -H "Content-Type: application/json" \
  -d '{"name":"TEST_POSE","angles":[45,60,90,120,30]}'

# Delete pose
curl -X DELETE http://localhost:8000/api/poses/TEST_POSE

# Health check
curl http://localhost:8000/health
```

---

## Sample Test Program

Create this block program to test all features:

```
forever
  if camera sees "red_small" with confidence > 70%
    move arm to pose PICKUP
    close claw
    wait 1 seconds
    move arm to pose DROP_ZONE
    open claw
    wait 0.5 seconds
```

**Expected generated code:**
```cpp
while (true) {
  Blynk.run();
  if (cameraSees("red_small", 70)) {
    moveArmToPose(POSE_PICKUP);
    closeClaw();
    delay(1000);
    moveArmToPose(POSE_DROP_ZONE);
    openClaw();
    delay(500);
  }
}
```

---

## Common Issues

### Browser shows blank page
- Check browser console (F12) for errors
- Verify server is running: `curl http://localhost:8000/health`
- Try hard refresh: Ctrl+F5

### Blockly not loading
- Check internet connection (Blockly loads from CDN)
- Check console for JavaScript errors
- Verify: `https://unpkg.com/blockly/blockly.min.js` is accessible

### Blocks don't snap together
- Some blocks are statements (have connectors top/bottom)
- Some blocks are values (have left connector, fit into slots)
- Logic: if/forever are statements, numbers/comparisons are values

### Build fails immediately
- arduino-cli not installed - see `docs/ARDUINO_CLI_SETUP.md`
- No settings configured - go to Setup tab first
- No blocks in workspace - add at least one block

### Settings don't save
- Check write permissions in `projects/` directory
- Check browser console for network errors
- Verify backend is running

---

## Performance Benchmarks

**Expected metrics:**
- Page load: < 2 seconds
- Blockly initialization: < 1 second
- API response time: < 100ms
- Build time (with arduino-cli): 30-60 seconds
- Generated code preview: Updates instantly

---

## Browser Compatibility

Tested and working:
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)

Not supported:
- ❌ Internet Explorer

---

## Next Steps After Testing

1. **Install arduino-cli** - Follow `docs/ARDUINO_CLI_SETUP.md`
2. **Test real compilation** - Build a simple program
3. **Flash to ESP32** - Follow `docs/FLASH_INSTRUCTIONS.md`
4. **Document hardware** - Update `docs/HARDWARE_PINOUT.md` with actual GPIO pins
5. **Test with robot** - Verify servos move correctly

---

## Quick Demo Script

**For showing the IDE to advisers/team:**

1. "This is the Setup tab - configure WiFi and Blynk" (fill form, save)
2. "Teach Poses tab - record robot positions" (save a pose)
3. "Program tab - drag blocks to create robot behavior" (build forever loop)
4. "Code preview shows generated C++ in real-time" (point to right panel)
5. "Click Build & Flash to compile firmware" (show modal)
6. "Download and flash to ESP32" (show download button)

**Demo takes ~3 minutes.**
