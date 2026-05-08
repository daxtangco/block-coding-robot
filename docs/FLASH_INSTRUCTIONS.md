# Flashing Instructions

This guide explains how to flash compiled firmware (.bin files) to your ESP32 boards.

## Prerequisites

### Install esptool

**Windows/macOS/Linux:**
```bash
pip install esptool
```

Verify installation:
```bash
esptool.py version
```

## Flashing ESP32 (Arm Controller)

### 1. Connect the Board
- Connect ESP32 to your computer via USB
- Note the COM port (Windows) or device path (macOS/Linux)

### Windows
Check Device Manager → Ports (COM & LPT) for "Silicon Labs CP210x" or similar

### macOS
```bash
ls /dev/cu.*
```
Look for `/dev/cu.usbserial-*` or `/dev/cu.SLAB_USBtoUART`

### Linux
```bash
ls /dev/tty*
```
Look for `/dev/ttyUSB0` or `/dev/ttyACM0`

### 2. Flash the Firmware

**Windows:**
```bash
esptool.py --chip esp32 --port COM3 --baud 921600 write_flash 0x10000 robot-firmware.bin
```

**macOS:**
```bash
esptool.py --chip esp32 --port /dev/cu.SLAB_USBtoUART --baud 921600 write_flash 0x10000 robot-firmware.bin
```

**Linux:**
```bash
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 921600 write_flash 0x10000 robot-firmware.bin
```

### 3. Monitor Serial Output (Optional)

To verify the firmware is running:

**Arduino IDE Serial Monitor:**
1. Open Arduino IDE
2. Tools → Port → Select your ESP32
3. Tools → Serial Monitor
4. Set baud rate to 115200

**Command line (screen):**
```bash
# macOS/Linux
screen /dev/cu.SLAB_USBtoUART 115200

# Linux alternative
screen /dev/ttyUSB0 115200
```

**Command line (PuTTY on Windows):**
1. Download PuTTY
2. Connection Type: Serial
3. Serial line: COM3 (your port)
4. Speed: 115200

## Flashing ESP32-CAM (Vision Board)

ESP32-CAM requires **manual boot mode** activation:

### 1. Enter Flash Mode
1. Connect GPIO 0 to GND (use jumper wire)
2. Press RESET button (or power cycle)
3. Board is now in flash mode

### 2. Flash Firmware
Use the same command as above, but change the port to ESP32-CAM's port.

### 3. Exit Flash Mode
1. Remove GPIO 0 to GND jumper
2. Press RESET button
3. Board will now run the firmware

## Troubleshooting

### "Could not open port"
- **Windows**: Check if another program (Arduino IDE, PuTTY) is using the port
- **Linux**: Add yourself to `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  ```
  Then log out and back in

### "Failed to connect to ESP32"
- Try holding BOOT button during flash
- Reduce baud rate: use `--baud 115200` instead of `921600`
- Check USB cable (some cables are power-only)

### "A fatal error occurred: Invalid head of packet"
- Wrong port selected
- Board not in flash mode (for ESP32-CAM)
- Try pressing and holding BOOT button

### Flash succeeds but board doesn't work
- Check WiFi credentials in settings are correct
- Check Blynk auth tokens
- Verify servos are connected to correct GPIO pins (see HARDWARE_PINOUT.md)
- Monitor serial output for error messages

## Quick Reference

| Flag | Purpose |
|------|---------|
| `--chip esp32` | Target chip type |
| `--port COM3` | Serial port |
| `--baud 921600` | Flash speed (slower = more reliable) |
| `write_flash` | Write mode |
| `0x10000` | Flash address for app partition |

## Advanced: Erasing Flash

To completely erase the ESP32 flash:
```bash
esptool.py --chip esp32 --port COM3 erase_flash
```

**Warning**: This removes all data including WiFi credentials and Blynk tokens.

## Next Steps

After flashing:
1. Open Blynk mobile app
2. Verify ESP32 appears online
3. Test manual control via sliders (V0-V4)
4. Toggle auto mode (V5) to run student program
