# Access Point Mode Setup Guide

## Overview

The robot runs as a WiFi Access Point, allowing direct phone connection without external WiFi or cloud services.

## Initial Setup (One-Time)

### 1. Flash Firmware

1. Connect ESP32 to laptop via USB
2. Open Desktop IDE: http://localhost:8000
3. Go to Setup tab
4. Click "Build & Flash"
5. Wait for compilation and upload (~2 minutes)

### 2. Upload PWA Files (One-Time)

Upload web interface files to ESP32:

```bash
python scripts/upload_spiffs.py --port COM3
```

Replace `COM3` with your ESP32's serial port.

### 3. Verify Setup

1. Unplug USB, power on ESP32
2. Check serial monitor for:
   ```
   Starting Robot Arm Controller (AP Mode)...
   SSID: RobotArm-XXXX
   Password: robot1234
   AP IP address: 192.168.4.1
   Ready! Connect to WiFi and open browser.
   ```

## Daily Use

### Connecting Phone to Robot

1. Power on robot (wait 5 seconds for boot)
2. Open phone WiFi settings
3. Connect to `RobotArm-XXXX` network
   - Password: `robot1234`
4. Browser opens automatically (captive portal)
5. Control interface appears

### Manual Control

- Move sliders to control servos (Base, Shoulder, Elbow, Wrist, Gripper)
- Mode toggle: Switch between Manual and Auto
- Reset button: Return all servos to default positions

### Running Programs

1. Create block program in Desktop IDE (laptop)
2. Click "Build & Flash" to upload
3. Connect phone to robot WiFi
4. Toggle "Auto" mode in control interface
5. Program runs automatically

## Troubleshooting

### Can't See Robot WiFi Network

**Check:**
- ESP32 is powered on (LED lit)
- Wait 10 seconds after power-on
- Phone WiFi is enabled
- Not connected to another "RobotArm" network

**Solution:**
- Restart ESP32
- Check serial monitor for errors
- Verify firmware was flashed successfully

### Browser Doesn't Open Automatically

**iOS:**
- Connect to network, wait 5 seconds
- If no popup, open Safari and go to any website
- Captive portal will redirect

**Android:**
- Connect to network
- Tap notification "Sign in to network"
- Or open Chrome and go to `192.168.4.1`

### Controls Don't Respond

**Check:**
- Connection status shows "Connected" (green dot)
- Check browser console for errors
- Verify servos have power (external 5V supply)

**Solution:**
- Refresh browser page
- Disconnect/reconnect WiFi
- Check serial monitor for WebSocket errors

### Multiple Robots in Classroom

Each robot has unique SSID (last 4 digits of MAC address):
- Robot A: `RobotArm-A4B2`
- Robot B: `RobotArm-C8D1`
- Robot C: `RobotArm-F3E9`

Students connect to their specific robot's network.

## Advanced Configuration

### Change AP Password

Edit `backend/templates/arm_controller_ap_mode.ino`:

```cpp
const char* AP_PASSWORD = "your-new-password";
```

Rebuild and flash firmware.

### Change Default Servo Positions

Edit `backend/templates/arm_controller_ap_mode.ino`:

```cpp
const int DEFAULT_POSITIONS[5] = {0, 60, 70, 60, 90};
//                                 ^  ^   ^   ^   ^
//                                 |  |   |   |   Gripper
//                                 |  |   |   Wrist
//                                 |  |   Elbow
//                                 |  Shoulder
//                                 Base
```

Rebuild and flash firmware.

## Technical Details

- **WiFi Standard:** 802.11 b/g/n (2.4GHz only)
- **IP Address:** 192.168.4.1 (fixed)
- **DHCP Range:** 192.168.4.2 - 192.168.4.10
- **WebSocket Port:** 80 (standard HTTP)
- **Max Clients:** 4-8 simultaneous connections
- **Range:** ~50 meters (typical indoor)
