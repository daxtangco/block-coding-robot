#!/bin/bash
# Quick Migration Script for WSL
# Automatically migrates LEGO detection training pipeline to WSL

set -e  # Exit on error

echo "======================================================================"
echo "LEGO Detection Training - WSL Migration Script"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running in WSL
if ! grep -qi microsoft /proc/version 2>/dev/null; then
    echo -e "${RED}✗ This script must be run in WSL!${NC}"
    echo "Open WSL terminal and run: bash migrate_to_wsl.sh"
    exit 1
fi

echo -e "${GREEN}✓ Running in WSL${NC}"
echo ""

# Step 1: Copy project to WSL home
echo "======================================================================"
echo "Step 1: Copying Project to WSL"
echo "======================================================================"

WINDOWS_PATH="/mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot"
WSL_PATH="$HOME/block-coding-robot"

if [ ! -d "$WINDOWS_PATH" ]; then
    echo -e "${RED}✗ Windows project not found at: $WINDOWS_PATH${NC}"
    echo "Please update WINDOWS_PATH in this script"
    exit 1
fi

if [ -d "$WSL_PATH" ]; then
    echo -e "${YELLOW}⚠ Project already exists at: $WSL_PATH${NC}"
    read -p "Overwrite? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old copy..."
        rm -rf "$WSL_PATH"
    else
        echo "Skipping copy..."
        cd "$WSL_PATH"
    fi
fi

if [ ! -d "$WSL_PATH" ]; then
    echo "Copying project files (excluding datasets)..."
    mkdir -p "$WSL_PATH"

    # Copy files excluding large directories
    rsync -av --progress \
        --exclude 'datasets/' \
        --exclude 'training_output/' \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude '.git/objects/' \
        "$WINDOWS_PATH/" "$WSL_PATH/"

    echo -e "${GREEN}✓ Project copied to: $WSL_PATH${NC}"
fi

cd "$WSL_PATH"
echo ""

# Step 2: Handle datasets
echo "======================================================================"
echo "Step 2: Setting Up Datasets"
echo "======================================================================"

echo "Choose dataset option:"
echo "  1) Symlink to Windows datasets (recommended - no copy, instant)"
echo "  2) Copy datasets to WSL (faster access, uses space)"
echo "  3) Skip datasets (download later)"
read -p "Enter choice (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        echo "Creating symlink to Windows datasets..."
        rm -rf datasets
        ln -s "$WINDOWS_PATH/datasets" datasets
        echo -e "${GREEN}✓ Datasets symlinked${NC}"
        ;;
    2)
        echo "Copying datasets (this may take 10-30 minutes)..."
        echo "Copying required folders only (excluding optional LEGO brick images v1)"
        mkdir -p datasets
        cp -rv "$WINDOWS_PATH/datasets/images" datasets/ 2>/dev/null || true
        cp -rv "$WINDOWS_PATH/datasets/YOLO_ready_txt_labels" datasets/ 2>/dev/null || true
        cp -rv "$WINDOWS_PATH/datasets/annotations" datasets/ 2>/dev/null || true
        echo -e "${GREEN}✓ Datasets copied${NC}"
        ;;
    3)
        echo -e "${YELLOW}⚠ Skipping datasets${NC}"
        echo "You'll need to download or copy datasets later"
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
echo ""

# Step 3: Update system packages
echo "======================================================================"
echo "Step 3: Updating System Packages"
echo "======================================================================"

echo "Updating apt repositories..."
sudo apt update -qq

echo "Installing required system packages..."
sudo apt install -y -qq python3 python3-pip python3-venv build-essential python3-dev

echo -e "${GREEN}✓ System packages installed${NC}"
echo ""

# Step 4: Install Python dependencies
echo "======================================================================"
echo "Step 4: Installing Python Dependencies"
echo "======================================================================"

if [ -f "requirements.txt" ]; then
    echo "Installing Python packages from requirements.txt..."
    pip3 install -q --upgrade pip
    pip3 install -q -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ requirements.txt not found${NC}"
fi
echo ""

# Step 5: Verify installation
echo "======================================================================"
echo "Step 5: Verifying Installation"
echo "======================================================================"

echo "Checking Python imports..."

# Test imports
python3 -c "import torch; print('  ✓ PyTorch:', torch.__version__)" 2>/dev/null || echo -e "${RED}  ✗ PyTorch not installed${NC}"
python3 -c "from ultralytics import YOLO; print('  ✓ Ultralytics YOLO: OK')" 2>/dev/null || echo -e "${RED}  ✗ Ultralytics not installed${NC}"
python3 -c "import cv2; print('  ✓ OpenCV:', cv2.__version__)" 2>/dev/null || echo -e "${RED}  ✗ OpenCV not installed${NC}"
python3 -c "from config import TARGET_CLASSES; print('  ✓ Config: OK (' + str(len(TARGET_CLASSES)) + ' classes)')" 2>/dev/null || echo -e "${YELLOW}  ⚠ Config import warning${NC}"

echo ""

# Step 6: Setup Git (if not configured)
echo "======================================================================"
echo "Step 6: Git Configuration"
echo "======================================================================"

if ! git config user.name > /dev/null 2>&1; then
    echo "Git user not configured"
    read -p "Enter your name: " git_name
    git config --global user.name "$git_name"
fi

if ! git config user.email > /dev/null 2>&1; then
    echo "Git email not configured"
    read -p "Enter your email: " git_email
    git config --global user.email "$git_email"
fi

echo "Git user: $(git config user.name)"
echo "Git email: $(git config user.email)"
echo -e "${GREEN}✓ Git configured${NC}"
echo ""

# Summary
echo "======================================================================"
echo "MIGRATION COMPLETE!"
echo "======================================================================"
echo ""
echo "Project location: $WSL_PATH"
echo "Datasets: $([ -L datasets ] && echo "Symlinked to Windows" || echo "Copied to WSL")"
echo ""
echo "Next steps:"
echo "  1. cd ~/block-coding-robot"
echo "  2. python3 prepare_datasets.py"
echo "  3. python3 train.py --experiment 2"
echo ""
echo "To access from Windows Explorer:"
echo "  \\\\wsl\$\\Ubuntu\\home\\$(whoami)\\block-coding-robot"
echo ""
echo -e "${GREEN}Happy training! 🚀${NC}"
