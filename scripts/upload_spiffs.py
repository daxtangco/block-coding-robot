#!/usr/bin/env python3
"""
Upload PWA files to ESP32 SPIFFS filesystem.

Usage: python scripts/upload_spiffs.py --port COM3
"""

import argparse
import subprocess
import sys
from pathlib import Path

def upload_spiffs(port: str):
    """Upload data folder to ESP32 SPIFFS."""
    data_dir = Path("data")

    if not data_dir.exists():
        print(f"Error: {data_dir} directory not found")
        return False

    print(f"Uploading SPIFFS from {data_dir} to {port}...")

    # Use ESP32 SPIFFS upload tool
    cmd = [
        "arduino-cli",
        "upload",
        "--fqbn", "esp32:esp32:esp32",
        "--port", port,
        "--input-dir", str(data_dir)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)

        if result.returncode == 0:
            print("✅ SPIFFS upload successful")
            return True
        else:
            print(f"❌ SPIFFS upload failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ arduino-cli not found. Please install it first.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload SPIFFS to ESP32")
    parser.add_argument("--port", required=True, help="Serial port (e.g., COM3, /dev/ttyUSB0)")
    args = parser.parse_args()

    success = upload_spiffs(args.port)
    sys.exit(0 if success else 1)
