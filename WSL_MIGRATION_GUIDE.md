# WSL Migration Guide

Migrate your LEGO detection training pipeline from Windows to WSL for better performance.

---

## 🎯 Why Migrate to WSL?

**Benefits:**
- ✅ **Faster training** (native Linux performance)
- ✅ **Better compatibility** with Python ML libraries
- ✅ **Easier package management** (apt, pip)
- ✅ **Native bash** (all scripts work perfectly)
- ✅ **Git integration** works smoothly

**Estimated migration time:** 15-30 minutes

---

## 📋 Prerequisites

### Check if WSL is Installed

Open **PowerShell** or **Command Prompt**:

```bash
wsl --version
```

**If installed:** You'll see version info
**If not installed:** See [Install WSL](#install-wsl-optional) below

---

### Check Your WSL Distribution

```bash
wsl -l -v
```

**Expected output:**
```
  NAME            STATE           VERSION
* Ubuntu          Running         2
```

---

## 🚀 Quick Migration (3 Steps)

### Step 1: Access Your Project from WSL

In **WSL terminal** (or run `wsl` from PowerShell):

```bash
# Windows C: drive is mounted at /mnt/c in WSL
cd /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot

# Verify files are there
ls -la
```

**You should see all your files!**

---

### Step 2: Copy to WSL Home Directory

```bash
# Copy entire project to WSL home
cp -r /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot ~/

# Navigate to WSL copy
cd ~/block-coding-robot

# Verify
ls -la
```

**Why copy?** Working in `/mnt/c` is slower. WSL's native filesystem (`~`) is much faster.

---

### Step 3: Set Up Python Environment in WSL

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install Python 3 and pip (if not already installed)
sudo apt install -y python3 python3-pip python3-venv

# Verify Python version
python3 --version

# Install dependencies
cd ~/block-coding-robot
pip3 install -r requirements.txt

# Verify installation
python3 setup_environment.py
```

---

## ✅ Verify Migration Success

### Check All Files Copied

```bash
cd ~/block-coding-robot

# Count Python files
ls *.py | wc -l
# Should show 8

# Check documentation
ls *.md | wc -l
# Should show multiple files

# Check datasets (if copied)
du -sh datasets/
# Should show size
```

---

### Test Import

```bash
# Test imports work
python3 -c "import torch; print('PyTorch:', torch.__version__)"
python3 -c "from ultralytics import YOLO; print('YOLO: OK')"
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
```

**All should print without errors.**

---

### Run a Quick Test

```bash
# Test configuration
python3 -c "from config import TARGET_CLASSES; print('Classes:', len(TARGET_CLASSES))"

# Should output: Classes: 8
```

---

## 📁 Dataset Migration Options

You have **3 options** for datasets (they're large):

### Option 1: Symlink (Recommended - No Copy)

Keep datasets on Windows, link to WSL:

```bash
cd ~/block-coding-robot

# Remove empty datasets folder if exists
rm -rf datasets

# Create symlink to Windows datasets
ln -s /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/datasets datasets

# Verify
ls -la datasets/
```

**Pros:**
- ✅ No disk space used
- ✅ Instant "migration"
- ✅ Changes sync automatically

**Cons:**
- ⚠️ Slightly slower than native WSL filesystem

---

### Option 2: Copy Datasets (Faster but Uses Space)

```bash
# Copy datasets to WSL (will take time)
cp -r /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/datasets ~/block-coding-robot/

# Or copy only required datasets (skip optional)
mkdir -p ~/block-coding-robot/datasets
cp -r /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/datasets/images ~/block-coding-robot/datasets/
cp -r /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/datasets/YOLO_ready_txt_labels ~/block-coding-robot/datasets/
cp -r /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/datasets/annotations ~/block-coding-robot/datasets/
```

**Time:** 10-30 minutes depending on dataset size

---

### Option 3: Download Datasets Directly in WSL

```bash
cd ~/block-coding-robot

# If datasets are from Kaggle
pip3 install kaggle

# Download directly (faster than copying)
# kaggle datasets download -d <dataset-name>
# unzip dataset.zip -d datasets/
```

---

## 🔧 Configure Git in WSL

### Set Up Git Identity

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

### Connect to GitHub

If using SSH:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: Settings → SSH Keys → New SSH key
```

If using HTTPS (simpler):

```bash
# Git will prompt for credentials
# Use Personal Access Token as password
```

---

### Verify Git Works

```bash
cd ~/block-coding-robot

# Check status
git status

# Pull latest changes
git pull origin main
```

---

## 🏃 Running Training in WSL

### Complete Workflow

```bash
cd ~/block-coding-robot

# 1. Setup environment (if not done)
python3 setup_environment.py

# 2. Prepare datasets
python3 prepare_datasets.py

# 3. Train model (Experiment 2 recommended)
python3 train.py --experiment 2

# 4. Validate
python3 validate.py --model training_output/models/experiment_2_*/stage2_finetuned/weights/best.pt --experiment 2

# 5. Test
python3 test.py --model <path-to-best.pt> --image datasets/images/00000.jpg --benchmark

# 6. Generate thesis graphs
python3 generate_thesis_graphs.py --exp2-results <path> --exp2-metrics <path>
```

---

## 💡 WSL Tips & Tricks

### Access WSL Files from Windows

In **Windows Explorer**, type:
```
\\wsl$\Ubuntu\home\YourUsername\block-coding-robot
```

Or click: "Linux" in left sidebar (Windows 11)

---

### Open WSL in VS Code

```bash
# In WSL terminal
cd ~/block-coding-robot
code .
```

VS Code will open with WSL integration!

---

### Run Windows Apps from WSL

```bash
# Open Windows Explorer in current directory
explorer.exe .

# Open file with Windows app
notepad.exe file.txt
```

---

### Check Disk Space

```bash
# Check available space
df -h ~

# Check folder size
du -sh ~/block-coding-robot
du -sh ~/block-coding-robot/datasets
```

---

### Monitor GPU Usage (if you have GPU)

```bash
# Install nvidia-smi in WSL
# (Requires NVIDIA GPU drivers + WSL2 + CUDA toolkit)
nvidia-smi -l 1
```

---

## 🔄 Sync Between Windows and WSL

### Option A: Work in WSL, Access from Windows

**Recommended for training:**

```bash
# Work in: ~/block-coding-robot (WSL native)
# Access from Windows: \\wsl$\Ubuntu\home\YourUsername\block-coding-robot
```

---

### Option B: Work in Windows, Run in WSL

**Recommended for development:**

```bash
# Work in: /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot (Windows)
# Run commands in WSL
cd /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot
python3 train.py --experiment 2
```

⚠️ **Slower** but convenient for editing in Windows apps.

---

### Option C: Git Sync (Best of Both)

```bash
# Edit in Windows or WSL
# Commit changes
git add .
git commit -m "Update"

# Pull changes in other environment
git pull
```

---

## ⚙️ Performance Comparison

| Task | Windows | WSL (via /mnt/c) | WSL Native (~) |
|------|---------|------------------|----------------|
| File I/O | Fast | Slow | **Fastest** |
| Training | Baseline | -20% | **+10-15%** |
| pip install | Baseline | Slower | **Faster** |

**Recommendation:** Use WSL native (`~/block-coding-robot`)

---

## 🆘 Troubleshooting

### Issue: Python not found

```bash
# Install Python
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

---

### Issue: Permission denied

```bash
# Make scripts executable
chmod +x ~/block-coding-robot/*.py
```

---

### Issue: Can't access Windows files

```bash
# Windows drives are mounted at /mnt/
ls /mnt/c/Users/
```

---

### Issue: Package installation fails

```bash
# Update pip
pip3 install --upgrade pip

# Install build tools
sudo apt install build-essential python3-dev
```

---

### Issue: Out of disk space in WSL

```bash
# Check space
df -h

# Clean apt cache
sudo apt clean
sudo apt autoremove

# Clean pip cache
pip3 cache purge

# Delete old training outputs
rm -rf ~/block-coding-robot/training_output/old_runs
```

---

### Issue: Git shows many modified files

```bash
# Fix line endings (Windows vs Linux)
cd ~/block-coding-robot
git config core.autocrlf input
git add --renormalize .
```

---

## 📊 Migration Checklist

- [ ] WSL installed and running
- [ ] Project copied to `~/block-coding-robot`
- [ ] Python 3 installed in WSL
- [ ] Dependencies installed (`requirements.txt`)
- [ ] Datasets accessible (symlink or copied)
- [ ] Git configured
- [ ] Test run successful (`python3 -c "import torch"`)
- [ ] Can run scripts (`python3 setup_environment.py`)

---

## 🎯 Quick Copy-Paste Commands

**Complete migration in one go:**

```bash
# Run in WSL terminal

# 1. Copy project
cp -r /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot ~/
cd ~/block-coding-robot

# 2. Symlink datasets (or copy if you prefer)
ln -s /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/datasets datasets

# 3. Update system
sudo apt update && sudo apt upgrade -y

# 4. Install Python dependencies
sudo apt install -y python3 python3-pip python3-venv build-essential
pip3 install -r requirements.txt

# 5. Setup environment
python3 setup_environment.py

# 6. Verify
python3 -c "import torch; from ultralytics import YOLO; import cv2; print('✓ All imports OK')"

echo "✓ Migration complete!"
echo "Project location: ~/block-coding-robot"
```

---

## 🚀 Next Steps After Migration

```bash
# You're now in WSL!

# Prepare datasets
python3 prepare_datasets.py

# Train model
python3 train.py --experiment 2

# Training will be faster in WSL native filesystem!
```

---

## 💾 Backup Strategy

**Keep both copies initially:**

- ✅ Windows: `C:\Users\DaxAxisTangco\Documents\block-coding-robot` (backup)
- ✅ WSL: `~/block-coding-robot` (working copy)

**Use Git for sync:**

```bash
# In WSL
cd ~/block-coding-robot
git add .
git commit -m "WSL training updates"
git push

# In Windows
cd C:\Users\DaxAxisTangco\Documents\block-coding-robot
git pull
```

---

## 📈 Expected Performance Gains

After migration to WSL native filesystem:

| Task | Windows | WSL Native | Improvement |
|------|---------|------------|-------------|
| File I/O | Baseline | 2-3x faster | +200% |
| pip install | Baseline | 1.5x faster | +50% |
| Training | Baseline | 1.1-1.2x faster | +10-20% |
| Dataset prep | Baseline | 2x faster | +100% |

**Overall: ~15-20% faster training!**

---

## ✅ Summary

**Migration Steps:**
1. Copy project to `~/block-coding-robot` in WSL
2. Symlink or copy datasets
3. Install dependencies
4. Run training

**Time required:**
- Copy files: 5-10 min
- Setup environment: 10-15 min
- Verify: 5 min
- **Total: ~30 min**

**Performance gain: ~15-20% faster training**

---

**Ready to migrate? Run the quick commands above!** 🚀
