# Arduino CLI Setup Guide

This guide walks you through installing and configuring `arduino-cli` for compiling ESP32 firmware.

## 1. Install Arduino CLI

### Windows
1. Download the latest release from [GitHub](https://github.com/arduino/arduino-cli/releases)
2. Extract `arduino-cli.exe` to a folder (e.g., `C:\Program Files\arduino-cli\`)
3. Add the folder to your PATH:
   - Search "Environment Variables" in Windows
   - Edit "Path" variable
   - Add the arduino-cli folder path
   - Restart your terminal

### macOS
```bash
brew install arduino-cli
```

### Linux
```bash
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
```

## 2. Initialize Configuration

```bash
arduino-cli config init
```

This creates a configuration file at:
- Windows: `%USERPROFILE%\.arduino15\arduino-cli.yaml`
- macOS/Linux: `~/.arduino15/arduino-cli.yaml`

## 3. Update Package Index

```bash
arduino-cli core update-index
```

## 4. Install ESP32 Core

```bash
arduino-cli core install esp32:esp32
```

This may take a few minutes as it downloads the ESP32 toolchain.

## 5. Install Required Libraries

```bash
arduino-cli lib install "Blynk"
arduino-cli lib install "ESP32Servo"
```

## 6. Verify Installation

List all ESP32 boards to confirm installation:

```bash
arduino-cli board listall esp32
```

You should see output like:
```
Board Name                         FQBN
AI Thinker ESP32-CAM              esp32:esp32:esp32cam
ESP32 Dev Module                  esp32:esp32:esp32
ESP32-S2 Dev Module               esp32:esp32:esp32s2
...
```

## 7. Test Compilation

Create a test sketch to verify everything works:

```bash
mkdir test-sketch
cd test-sketch
echo 'void setup() { Serial.begin(115200); }
void loop() { delay(1000); }' > test-sketch.ino
```

Compile it:
```bash
arduino-cli compile --fqbn esp32:esp32:esp32 .
```

If successful, you'll see "Sketch uses X bytes..." output.

## Troubleshooting

### "arduino-cli: command not found"
- Verify arduino-cli is in your PATH
- Restart your terminal after adding to PATH

### ESP32 core install fails
- Check your internet connection
- Try: `arduino-cli core update-index --additional-urls https://dl.espressif.com/dl/package_esp32_index.json`

### Library install fails
- Update package index: `arduino-cli core update-index`
- Search for library: `arduino-cli lib search <library-name>`

### Permission errors (Linux/macOS)
- You may need to add yourself to the `dialout` group:
  ```bash
  sudo usermod -a -G dialout $USER
  ```
- Log out and back in for changes to take effect

## Board-Specific FQBNs

For the Block Robot IDE project:
- **Arm Controller (ESP32 Dev Module)**: `esp32:esp32:esp32`
- **Vision Board (ESP32-CAM)**: `esp32:esp32:esp32cam`

## Next Steps

Once setup is complete, the Block Robot IDE backend will use arduino-cli to compile student-generated code automatically.
