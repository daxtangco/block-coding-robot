# Access Point Mode Troubleshooting

## Connection Issues

### Problem: Can't find RobotArm-XXXX network

**Possible causes:**
- ESP32 not powered on
- Firmware not flashed
- ESP32 crashed during boot

**Solutions:**
1. Check ESP32 power LED is on
2. Connect via USB and check serial monitor:
   ```bash
   python -m serial.tools.miniterm COM3 115200
   ```
   Expected output:
   ```
   Starting Robot Arm Controller (AP Mode)...
   SSID: RobotArm-XXXX
   ```
3. If no output, reflash firmware
4. Try power cycle (unplug/replug USB)

### Problem: Connected to WiFi but no browser popup

**iOS:**
- Wait 5-10 seconds after connecting
- Open Safari, go to any website (will redirect)
- Check Settings → WiFi → "i" icon → "Use This Connection" is enabled

**Android:**
- Look for notification "Sign in to network" and tap it
- Or open Chrome and manually go to `192.168.4.1`
- Check Settings → WiFi → Advanced → "Auto-connect to captive portals"

### Problem: Connection status shows "Disconnected"

**Check:**
1. WebSocket connection failed
2. Open browser console (F12 or inspect)
3. Look for errors like:
   - `WebSocket connection to 'ws://192.168.4.1/ws' failed`
   - `ERR_CONNECTION_REFUSED`

**Solutions:**
- Refresh page (F5 or pull down)
- Clear browser cache
- Check serial monitor for WebSocket errors
- Verify SPIFFS was uploaded:
  ```bash
  python scripts/upload_spiffs.py --port COM3
  ```

## Control Issues

### Problem: Sliders move but servos don't

**Check:**
1. External 5V power supply connected to PCA9685
2. Ground shared between ESP32 and power supply
3. I2C connections (GPIO 21 SDA, GPIO 22 SCL)

**Solutions:**
- Verify PCA9685 wiring (see docs/PCA9685_WIRING_GUIDE.md)
- Check serial monitor for I2C errors
- Test single servo:
  ```cpp
  pwm.setPWM(0, 0, 300);  // Should move servo 0
  ```

### Problem: One servo doesn't respond

**Check:**
1. Servo plugged into correct channel (0-4)
2. Servo power wire connected
3. That specific PCA9685 channel working

**Solutions:**
- Swap servo to different channel
- Try known-working servo in that channel
- Check PCA9685 channel LED indicator

### Problem: Servos jitter or twitch

**Possible causes:**
- Insufficient power supply current
- Loose wiring
- Multiple commands sent too fast

**Solutions:**
- Use 5V 2A+ power supply
- Check all connections are secure
- Add delay between servo movements:
  ```cpp
  delay(50);  // 50ms between commands
  ```

## Auto Mode Issues

### Problem: Toggle to Auto but program doesn't run

**Check:**
1. Block code was compiled into firmware
2. Serial monitor shows "Auto mode ON"
3. Student program has no errors

**Solutions:**
- Verify `runStudentProgram()` contains code:
  ```bash
  grep "runStudentProgram" builds/*/sketch/sketch.ino
  ```
- Check for infinite loops in student code
- Add debug prints:
  ```cpp
  void runStudentProgram() {
    Serial.println("Running student program");
    // Your code here
  }
  ```

### Problem: Auto mode runs but servos don't move

**Check:**
- Student code calls servo functions correctly
- Pose definitions are valid
- No blocking delays in code

**Debug:**
Add serial prints to student code:
```cpp
Serial.println("Moving to pose 1");
moveArmToPose(POSE_HOME);
Serial.println("Pose 1 complete");
```

## Performance Issues

### Problem: High latency (>200ms)

**Possible causes:**
- Too many WebSocket clients connected
- WiFi interference from other networks
- ESP32 overloaded

**Solutions:**
- Limit to 2-3 clients per robot
- Change AP channel:
  ```cpp
  WiFi.softAP(ssid, password, channel);  // Try channels 1, 6, 11
  ```
- Reduce broadcast frequency

### Problem: WebSocket disconnects frequently

**Check:**
1. Phone power saving mode
2. Phone goes to sleep
3. Distance from robot

**Solutions:**
- Disable phone sleep/battery saver
- Stay within 10 meters of robot
- Add keepalive pings (optional)

## Build/Flash Issues

### Problem: Compilation fails

**Error:** `ESPAsyncWebServer.h: No such file or directory`

**Solution:**
Install required libraries:
```bash
arduino-cli lib install "ESP Async WebServer"
arduino-cli lib install "AsyncTCP"
```

**Error:** `SPIFFS.h: No such file or directory`

**Solution:**
SPIFFS is included with ESP32 core. Update core:
```bash
arduino-cli core update-index
arduino-cli core upgrade esp32:esp32
```

### Problem: SPIFFS upload fails

**Error:** `esptool.py not found`

**Solution:**
Install esptool:
```bash
pip install esptool
```

**Error:** `data folder not found`

**Solution:**
Ensure PWA files exist:
```bash
ls -la data/
```
Should show: index.html, style.css, app.js, manifest.json, icons

## Classroom Issues

### Problem: Multiple robots interfere

**Note:** Each robot has unique SSID (MAC-based), so interference is rare.

**If interference occurs:**
1. Check SSIDs are unique:
   - Connect to each robot via USB
   - Check serial monitor for SSID
2. Change AP channel per robot (1, 6, 11)
3. Space robots at least 2 meters apart

### Problem: Students connect to wrong robot

**Solution:**
Label each robot with its SSID:
```
Robot #1: RobotArm-A4B2
Robot #2: RobotArm-C8D1
Robot #3: RobotArm-F3E9
```

Students verify connection in control interface.

## Getting More Help

### Check Serial Monitor

Always check serial output when troubleshooting:
```bash
python -m serial.tools.miniterm COM3 115200
```

Useful output:
- WiFi status
- WebSocket connections
- Servo commands
- Error messages

### Enable Debug Logging

Edit firmware template, add:
```cpp
#define DEBUG_WEBSOCKET
```

Then in WebSocket handler:
```cpp
#ifdef DEBUG_WEBSOCKET
  Serial.printf("WS: Received %d bytes from client #%u\n", len, client->id());
#endif
```

### Reset to Factory Defaults

If all else fails:
1. Erase ESP32 flash:
   ```bash
   esptool.py --chip esp32 --port COM3 erase_flash
   ```
2. Reflash firmware (see AP_MODE_SETUP.md)
3. Re-upload SPIFFS
4. Test with single phone connection
