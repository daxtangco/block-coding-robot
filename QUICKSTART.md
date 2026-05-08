# Quick Start Testing Guide

## 🚀 Running the IDE

### 1. Start the Server
```bash
cd C:\Users\DaxAxisTangco\Documents\block-coding-robot
python -m uvicorn backend.main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### 2. Open Browser
Navigate to: **http://localhost:8000**

---

## ✅ 5-Minute Test Checklist

### Test 1: Setup Tab (WiFi & Blynk Config)
1. Click **"Setup"** tab
2. Fill in the form:
   - WiFi SSID: `TestNetwork`
   - WiFi Password: `password123`
   - Blynk Template ID: `TMPL123456789`
   - Blynk Template Name: `Robot Test`
   - Blynk Auth Token: `test_token_12345`
3. Click **"💾 Save Settings"**
4. ✅ Green success message appears
5. Click **"🔄 Reload"**
6. ✅ Form still shows your values

**Verify:** Check file created:
```bash
cat projects/default/settings.json
```

---

### Test 2: Teach Poses Tab
1. Click **"Teach Poses"** tab
2. Drag the sliders:
   - Base: 45°
   - Shoulder: 60°
   - Elbow: 90°
   - Wrist: 120°
   - Gripper: 30°
3. Click **"💾 Save Current Pose"**
4. Enter name: `PICKUP`
5. Click OK
6. ✅ Pose card appears showing `PICKUP [45, 60, 90, 120, 30]`
7. Create another pose named `DROP_ZONE` with different angles
8. ✅ Both poses appear in grid
9. Try clicking 🗑️ on one (not HOME)
10. ✅ Pose deletes

**Verify:** Status bar shows "2 poses" or "3 poses"

---

### Test 3: Program Tab (Block Coding)
1. Click **"Program"** tab
2. You see:
   - Left: Blockly editor with colored categories
   - Right: Code preview panel

3. **Drag blocks from toolbox:**

   From **Arm Control** (blue):
   - Drag **"move arm to pose"** → Click dropdown
   - ✅ See HOME, PICKUP, DROP_ZONE in list
   
   From **Logic** (green):
   - Drag **"forever"** block
   - Drag **"if"** block inside forever
   
   From **Vision** (purple):
   - Drag **"camera sees"** → Drop into "if" condition
   - Set class: "red_small"
   - Set confidence: 70
   
   From **Arm Control**:
   - Drag **"move arm to pose PICKUP"** into "if" body
   - Drag **"close claw"** below it
   - Drag **"wait 1 seconds"** from Logic
   - Drag **"move arm to pose DROP_ZONE"**
   - Drag **"open claw"**

4. **Check right panel:**
   ```cpp
   while (true) {
     Blynk.run();
     if (cameraSees("red_small", 70)) {
       moveArmToPose(POSE_PICKUP);
       closeClaw();
       delay(1000);
       moveArmToPose(POSE_DROP_ZONE);
       openClaw();
     }
   }
   ```

5. ✅ Code updates as you add/move blocks
6. ✅ Status bar shows "7 blocks" (or similar)

---

### Test 4: Build Button
1. With blocks in workspace, click **"🔨 Build & Flash"** in header
2. ✅ Modal dialog appears with spinner
3. You'll see one of two outcomes:

   **Without arduino-cli (Expected):**
   - ❌ Error: "arduino-cli not found..."
   - Shows helpful instructions
   - ✅ This is normal! UI works correctly

   **With arduino-cli installed:**
   - ✅ "Compiling your program..." message
   - Wait 30-60 seconds
   - ✅ "Build Successful!" with download button
   - Click download → get .bin file

4. Close modal by clicking X or outside

---

### Test 5: API Endpoints
Run these commands in a new terminal:

```bash
# Health check
curl http://localhost:8000/health

# Get current settings
curl http://localhost:8000/api/settings

# Get saved poses
curl http://localhost:8000/api/poses
```

✅ All should return JSON responses

---

## 🎯 Expected Behavior Summary

| Feature | Expected Result |
|---------|----------------|
| Server starts | Shows "Uvicorn running" message |
| Browser loads IDE | Professional UI with 3 tabs |
| Setup saves | Green success message, data persists |
| Pose sliders | Angles update in real-time |
| Pose saves | Cards appear immediately |
| Blocks snap | Visual feedback, code generates |
| Code preview | Updates instantly as blocks change |
| Build button | Modal appears, shows status |
| Status bar | Live counts update |

---

## ❌ If Something Goes Wrong

### Server won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Try different port
python -m uvicorn backend.main:app --port 8001
```

### Browser shows blank page
- Press F12 → Check Console for errors
- Try hard refresh: Ctrl + Shift + R
- Verify server is running: `curl http://localhost:8000/health`

### Blocks don't load
- Check internet connection (Blockly loads from CDN)
- Look for red errors in browser console (F12)
- Clear browser cache

### Settings won't save
- Check `projects/` folder exists and is writable
- Look at terminal for Python errors
- Check browser Network tab (F12) for API errors

### Build fails immediately
- arduino-cli not installed (expected - see docs/ARDUINO_CLI_SETUP.md)
- No settings configured (go to Setup tab first)
- No blocks in workspace (add at least one block)

---

## 📊 Performance Expectations

- **Page load:** < 2 seconds
- **Blockly init:** < 1 second  
- **API calls:** < 100ms
- **Code preview:** Instant
- **Build time:** 30-60 seconds (with arduino-cli)

---

## 🎬 Demo Script (2 minutes)

For showing the IDE to team/advisers:

1. "Setup tab - configure WiFi and Blynk" *[fill form, save]*
2. "Teach Poses - record robot positions" *[move sliders, save as PICKUP]*
3. "Program tab - drag blocks to create behavior" *[build forever + if + camera sees]*
4. "Real-time code preview shows generated C++" *[point to right panel]*
5. "Build & Flash compiles firmware" *[click button, show modal]*
6. "Download and flash to ESP32" *[show download or explain arduino-cli needed]*

**Total time: 2-3 minutes**

---

## Next Steps After Basic Testing

1. ✅ IDE works with test data
2. 📦 Install arduino-cli (see docs/ARDUINO_CLI_SETUP.md)
3. 🔨 Test actual firmware compilation
4. 🤖 Document hardware GPIO pins when available
5. 📸 Replace mock vision with TFLite model
6. 🧪 End-to-end robot testing

---

## Quick Commands Reference

```bash
# Start server
python -m uvicorn backend.main:app --reload

# Start in background (Windows)
start /b python -m uvicorn backend.main:app

# Check server status
curl http://localhost:8000/health

# View settings file
cat projects/default/settings.json

# View poses file
cat projects/default/poses.json

# Stop server
Ctrl + C
```

---

**Ready?** Start the server and open http://localhost:8000 🚀
