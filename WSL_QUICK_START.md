# WSL Quick Start - One Page

Fastest way to migrate and run training in WSL.

---

## ⚡ Super Quick Migration (2 Commands)

### Option 1: Automated Script

```bash
# Open WSL terminal (type 'wsl' in PowerShell or search 'Ubuntu')
cd /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot
bash migrate_to_wsl.sh
```

**Done!** Script handles everything automatically.

---

### Option 2: Manual (5 Commands)

```bash
# 1. Copy project to WSL
cp -r /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot ~/
cd ~/block-coding-robot

# 2. Symlink datasets (no copy needed)
ln -s /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/datasets datasets

# 3. Install dependencies
sudo apt update && sudo apt install -y python3 python3-pip build-essential
pip3 install -r requirements.txt

# 4. Verify
python3 -c "import torch; from ultralytics import YOLO; print('✓ Ready!')"
```

**Done!** Ready to train.

---

## 🚀 Train Model

```bash
cd ~/block-coding-robot

# Prepare datasets (10-15 min)
python3 prepare_datasets.py

# Train (2-5 hrs with GPU, 15-30 hrs CPU)
python3 train.py --experiment 2

# Validate
python3 validate.py --model training_output/models/experiment_2_*/stage2_finetuned/weights/best.pt --experiment 2
```

---

## 📁 File Locations

| Location | Path | Use For |
|----------|------|---------|
| **Windows** | `C:\Users\DaxAxisTangco\Documents\block-coding-robot` | Editing, backup |
| **WSL from Windows** | `\\wsl$\Ubuntu\home\YourUsername\block-coding-robot` | Browse in Explorer |
| **WSL from WSL** | `~/block-coding-robot` | Training, running scripts |
| **Windows from WSL** | `/mnt/c/Users/DaxAxisTangco/Documents/` | Access Windows files |

---

## 💡 Essential Commands

```bash
# Navigate between systems
cd ~/block-coding-robot              # WSL project
cd /mnt/c/Users/DaxAxisTangco/...    # Windows files

# Open in VS Code
code .                                # Opens in VS Code with WSL

# Open Windows Explorer
explorer.exe .                        # Opens current folder in Explorer

# Check disk space
df -h ~

# Check GPU (if available)
nvidia-smi
```

---

## 🔄 Sync Work Between Windows & WSL

**Method 1: Git (Recommended)**
```bash
# In WSL (after changes)
git add .
git commit -m "Training updates"
git push

# In Windows
git pull
```

**Method 2: Direct Access**
- Edit files in Windows: `\\wsl$\Ubuntu\home\YourUsername\block-coding-robot`
- Run scripts in WSL: `cd ~/block-coding-robot && python3 train.py`

---

## ⚠️ Common Issues

| Problem | Solution |
|---------|----------|
| `wsl` command not found | Install WSL: `wsl --install` in PowerShell |
| Permission denied | `chmod +x *.py` or run with `python3` |
| Python not found | `sudo apt install python3 python3-pip` |
| Can't see Windows files | Use `/mnt/c/Users/...` |
| Training slow | Make sure you're in `~/` not `/mnt/c/` |

---

## 📊 Performance

| Task | Windows | WSL (/mnt/c) | WSL (~) |
|------|---------|--------------|---------|
| Training | Baseline | -10% | **+15%** ⚡ |
| File I/O | Baseline | -50% | **+200%** ⚡ |

**Use WSL native (`~/`) for best performance!**

---

## ✅ Checklist

- [ ] WSL installed (`wsl --version`)
- [ ] Project copied to `~/block-coding-robot`
- [ ] Dependencies installed
- [ ] Can import torch: `python3 -c "import torch"`
- [ ] Datasets accessible
- [ ] Ready to train!

---

## 🎯 TL;DR

```bash
# Complete migration + training in WSL:

wsl                                   # Open WSL
bash /mnt/c/Users/DaxAxisTangco/Documents/block-coding-robot/migrate_to_wsl.sh
cd ~/block-coding-robot
python3 prepare_datasets.py
python3 train.py --experiment 2
```

**That's it!** 🚀

---

**See `WSL_MIGRATION_GUIDE.md` for detailed instructions.**
