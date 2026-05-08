#!/usr/bin/env python3
"""
Environment Setup Script for LEGO Object Detection Training
Sets up Python environment with required dependencies for YOLOv8 training
"""

import subprocess
import sys
import platform

def check_python_version():
    """Verify Python version is 3.8+"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8+ required")
        sys.exit(1)
    print("✓ Python version OK")

def install_requirements():
    """Install required packages"""
    requirements = [
        "ultralytics>=8.0.0",
        "torch>=2.0.0",
        "torchvision>=0.15.0",
        "opencv-python>=4.8.0",
        "pillow>=10.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "pyyaml>=6.0",
        "tqdm>=4.65.0",
        "scikit-learn>=1.3.0",
        "xmltodict>=0.13.0",
        "tensorboard>=2.13.0",
    ]

    print("\nInstalling required packages...")
    print("This may take several minutes...\n")

    for package in requirements:
        print(f"Installing {package}...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package, "--upgrade"
            ], stdout=subprocess.DEVNULL)
            print(f"✓ {package} installed")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")
            return False

    return True

def verify_installation():
    """Verify key packages are installed correctly"""
    print("\nVerifying installation...")

    try:
        import torch
        print(f"✓ PyTorch {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"  CUDA version: {torch.version.cuda}")
            print(f"  GPU device: {torch.cuda.get_device_name(0)}")
        else:
            print("  Training will use CPU (slower)")
    except ImportError:
        print("✗ PyTorch not found")
        return False

    try:
        import ultralytics
        print(f"✓ Ultralytics {ultralytics.__version__}")
    except ImportError:
        print("✗ Ultralytics not found")
        return False

    try:
        import cv2
        print(f"✓ OpenCV {cv2.__version__}")
    except ImportError:
        print("✗ OpenCV not found")
        return False

    return True

def main():
    """Main setup routine"""
    print("=" * 60)
    print("LEGO Object Detection - Environment Setup")
    print("=" * 60)
    print()

    # Check Python version
    check_python_version()
    print()

    # Show system info
    print(f"Operating System: {platform.system()} {platform.release()}")
    print(f"Architecture: {platform.machine()}")
    print()

    # Install packages
    if not install_requirements():
        print("\n✗ Installation failed")
        sys.exit(1)

    print()

    # Verify installation
    if not verify_installation():
        print("\n✗ Verification failed")
        sys.exit(1)

    print()
    print("=" * 60)
    print("✓ Environment setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run: python prepare_datasets.py")
    print("2. Run: python train.py --experiment 1")

if __name__ == "__main__":
    main()
