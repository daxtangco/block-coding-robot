#!/usr/bin/env python3
"""
Upload PWA files to ESP32 SPIFFS filesystem.

Usage: python scripts/upload_spiffs.py --port COM3
"""

import argparse
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

def upload_spiffs(port: str):
    """Upload data folder to ESP32 SPIFFS."""
    data_dir = Path("data")

    if not data_dir.exists():
        print(f"❌ Error: {data_dir} directory not found")
        return False

    print(f"📁 Found data directory with {len(list(data_dir.glob('*')))} files")
    print(f"⏳ Building SPIFFS image from {data_dir}...")

    # Create SPIFFS image using mkspiffs
    spiffs_image = Path(tempfile.gettempdir()) / "spiffs.bin"

    # Try mkspiffs first (if available)
    mkspiffs_cmd = [
        "mkspiffs",
        "-c", str(data_dir),
        "-s", "0x170000",  # SPIFFS size (1.5MB)
        "-p", "256",        # Page size
        "-b", "4096",       # Block size
        str(spiffs_image)
    ]

    try:
        print("🔨 Creating SPIFFS image with mkspiffs...")
        result = subprocess.run(mkspiffs_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  mkspiffs not found or failed, trying alternative method...")
            # mkspiffs not available, we'll use esptool to write individual files
            return upload_with_littlefs_gen(data_dir, port)
    except FileNotFoundError:
        print("⚠️  mkspiffs not installed, using alternative method...")
        return upload_with_littlefs_gen(data_dir, port)

    # Upload SPIFFS image using esptool
    print(f"📤 Uploading SPIFFS image to {port}...")
    esptool_cmd = [
        "python", "-m", "esptool",
        "--chip", "esp32",
        "--port", port,
        "--baud", "921600",
        "--before", "default_reset",
        "--after", "hard_reset",
        "write_flash",
        "0x290000",  # SPIFFS partition offset
        str(spiffs_image)
    ]

    try:
        result = subprocess.run(esptool_cmd, capture_output=True, text=True)
        print(result.stdout)

        if result.returncode == 0:
            print("✅ SPIFFS upload successful!")
            print("🔄 ESP32 will restart automatically")
            spiffs_image.unlink()  # Clean up temp file
            return True
        else:
            print(f"❌ Upload failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False

def upload_with_littlefs_gen(data_dir: Path, port: str):
    """Alternative: Use mklittlefs or manual upload."""
    print("❌ SPIFFS image creation requires 'mkspiffs' tool")
    print("\nInstallation instructions:")
    print("1. Download mkspiffs from: https://github.com/igrr/mkspiffs/releases")
    print("2. Add mkspiffs to your PATH")
    print("\nAlternative: Use PlatformIO which includes SPIFFS upload:")
    print("  pio run --target uploadfs")
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload SPIFFS to ESP32")
    parser.add_argument("--port", required=True, help="Serial port (e.g., COM3, /dev/ttyUSB0)")
    args = parser.parse_args()

    success = upload_spiffs(args.port)
    sys.exit(0 if success else 1)
