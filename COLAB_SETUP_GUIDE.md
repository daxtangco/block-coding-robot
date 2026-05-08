# Google Colab Setup Guide for LEGO Detection Training

Train your LEGO detection model on Google Colab's **free GPU** for faster training (2-5 hours instead of 15-30 hours).

---

## 🚀 Quick Start

### Step 1: Open Notebook in Colab

**Option A: Direct Upload**
1. Go to [Google Colab](https://colab.research.google.com/)
2. File → Upload notebook
3. Upload `LEGO_Detection_Training.ipynb`

**Option B: From GitHub (if you've pushed your code)**
1. Go to [Google Colab](https://colab.research.google.com/)
2. File → Open notebook → GitHub
3. Enter your repository URL
4. Open `LEGO_Detection_Training.ipynb`

---

### Step 2: Enable GPU

**IMPORTANT:** Enable GPU for faster training!

1. In Colab: **Runtime** → **Change runtime type**
2. Hardware accelerator: **GPU**
3. GPU type: **T4** (free tier)
4. Click **Save**

You should see: "Connected to Python 3 Google Compute Engine backend (GPU)"

---

### Step 3: Upload Project to Google Drive

**Method 1: Upload via Google Drive Web**

1. Compress your project folder (exclude large files):
   ```bash
   # On your local machine
   cd Documents/
   zip -r block-coding-robot.zip block-coding-robot/ -x "*/training_output/*" "*/builds/*" "*/__pycache__/*"
   ```

2. Upload `block-coding-robot.zip` to Google Drive:
   - Go to [Google Drive](https://drive.google.com/)
   - Create folder: `My Drive/block-coding-robot/`
   - Upload the zip file
   - Right-click → Extract

3. Upload datasets separately:
   - Compress `datasets` folder
   - Upload to `My Drive/block-coding-robot/datasets/`
   - Extract

**Method 2: Upload via Colab**

Run this in a Colab cell:
```python
from google.colab import files
uploaded = files.upload()  # Select your zip file
!unzip -q block-coding-robot.zip
```

---

## 📁 Expected Google Drive Structure

```
My Drive/
└── block-coding-robot/
    ├── config.py
    ├── prepare_datasets.py
    ├── train.py
    ├── validate.py
    ├── test.py
    ├── export_model.py
    ├── requirements.txt
    └── datasets/
        ├── images/
        ├── YOLO_ready_txt_labels/
        ├── annotations/
        └── LEGO brick images v1/
```

---

## 🎯 Running the Notebook

### Cell-by-Cell Execution

Run cells in order (Shift+Enter to run each cell):

1. **Mount Google Drive** - Connect to your Drive
2. **Check GPU** - Verify GPU is enabled
3. **Install Dependencies** - Install YOLOv8 and libraries
4. **Setup Project** - Navigate to project folder
5. **Check Datasets** - Verify datasets are present
6. **Prepare Datasets** - Process and validate (5-15 min)
7. **Train Experiment 1** - Optional baseline (1-2 hrs)
8. **Train Experiment 2** - Recommended (2-4 hrs) ⭐
9. **Validate Models** - Check performance
10. **Test & Visualize** - Run inference
11. **Export Model** - Convert to TFLite
12. **Download Results** - Save to local machine

---

## ⏱️ Expected Training Time on Colab

| Experiment | CPU Time | GPU Time (T4) |
|------------|----------|---------------|
| Dataset Prep | 10 min | 10 min |
| Experiment 1 | 10-20 hrs | 1-2 hrs |
| Experiment 2 | 15-30 hrs | 2-4 hrs |
| **Total** | **25-50 hrs** | **3-6 hrs** |

**With GPU: ~4 hours total** ⚡

---

## 💾 Saving Your Work

### Automatic Save to Google Drive

All outputs are saved to Google Drive:
```
/content/drive/MyDrive/block-coding-robot/training_output/
├── prepared_datasets/
├── models/
│   └── experiment_2_TIMESTAMP/
│       └── stage2_finetuned/
│           └── weights/
│               └── best.pt    ← YOUR TRAINED MODEL
└── results/
```

### Manual Download

Before your session ends:

```python
# Zip all results
!zip -r results.zip training_output/

# Download
from google.colab import files
files.download('results.zip')
```

---

## ⚠️ Important Colab Limitations

### 1. Session Timeout
- **Free tier**: 12-hour maximum session
- **Solution**: Save frequently to Google Drive
- Models are auto-saved after each epoch

### 2. GPU Quota
- **Free tier**: Limited GPU hours per day
- **Solution**: Train during off-peak hours
- Use CPU if GPU unavailable

### 3. Disconnection
- **Colab may disconnect** if idle
- **Solution**: Keep tab active, run this cell:
  ```python
  # Keep session alive
  import time
  while True:
      time.sleep(3600)  # Ping every hour
  ```

### 4. Storage Limit
- **Colab disk**: ~100GB temporary
- **Google Drive**: 15GB free tier
- **Solution**: Delete old experiments

---

## 🔧 Troubleshooting

### Problem: GPU Not Available

**Error:** "CUDA available: False"

**Solution:**
1. Runtime → Change runtime type → GPU → Save
2. Runtime → Restart runtime
3. Re-run cells from the start

---

### Problem: Out of Memory (OOM)

**Error:** "RuntimeError: CUDA out of memory"

**Solution 1 - Reduce Batch Size:**
```python
# Edit config.py in Colab
!sed -i 's/"batch": 16/"batch": 8/g' config.py
```

**Solution 2 - Clear GPU Memory:**
```python
import torch
torch.cuda.empty_cache()
```

---

### Problem: Session Disconnected

**Error:** Session crashed or disconnected during training

**Solution:**
- Training progress is saved every epoch
- Your model checkpoints are in Google Drive
- Resume training from `last.pt`:
  ```python
  !python train.py --experiment 2 --resume training_output/models/experiment_2_*/stage2_finetuned/weights/last.pt
  ```

---

### Problem: Can't Find Files

**Error:** "File not found" or "No such file or directory"

**Solution:**
1. Check path in Colab:
   ```python
   !ls /content/drive/MyDrive/block-coding-robot/
   ```
2. Update PROJECT_PATH in notebook
3. Re-upload datasets to correct location

---

### Problem: Slow Upload to Drive

**Solution:**
- Compress datasets before upload
- Use stable internet connection
- Upload during off-peak hours
- Alternative: Use Kaggle datasets (if available)

---

## 📊 Monitoring Training

### TensorBoard in Colab

```python
# Load TensorBoard extension
%load_ext tensorboard

# Start TensorBoard
%tensorboard --logdir training_output/models/
```

View training progress in real-time!

---

### Check Training Progress

```python
# View latest metrics
!tail -10 training_output/models/experiment_2_*/stage2_finetuned/results.csv
```

---

## 🎓 After Training

### Download Key Files

```python
from google.colab import files

# Download trained model
files.download('training_output/models/experiment_2_TIMESTAMP/stage2_finetuned/weights/best.pt')

# Download metrics
files.download('training_output/results/validation_best/metrics.json')

# Download graphs
files.download('training_output/results/validation_best/per_class_performance.png')
```

---

### Transfer to Local Machine

**Option 1: Direct Download from Colab**
- Right-click file in file browser → Download

**Option 2: Sync from Google Drive**
- Install Google Drive for Desktop
- Files sync automatically

**Option 3: Zip and Download**
```python
!zip -r lego_model.zip training_output/models/experiment_2_*/stage2_finetuned/
from google.colab import files
files.download('lego_model.zip')
```

---

## 🆓 Colab Free Tier vs Pro

| Feature | Free | Pro ($10/month) |
|---------|------|-----------------|
| GPU Access | Limited hours | Priority access |
| Session Length | 12 hours max | 24 hours max |
| GPU Type | T4 (16GB) | T4, P100, V100 |
| Background Execution | No | Yes |
| Speed | Standard | Faster |

**For thesis project:** Free tier is sufficient (4-6 hours total)

---

## 📝 Colab Tips & Tricks

### 1. Keyboard Shortcuts
- `Ctrl+Enter` - Run cell
- `Shift+Enter` - Run cell and move to next
- `Ctrl+M B` - Insert cell below
- `Ctrl+M A` - Insert cell above

### 2. Magic Commands
```python
%cd /path/to/directory    # Change directory
!ls                        # Run shell command
%time command             # Time execution
%load_ext tensorboard     # Load extension
```

### 3. Keep Colab Alive
```javascript
// Run in browser console (F12)
setInterval(() => {
  document.querySelector('colab-connect-button').click();
}, 60000);
```

### 4. Monitor GPU Usage
```python
!nvidia-smi -l 1  # Update every second
```

### 5. Check Disk Space
```python
!df -h
```

---

## 🔄 Alternative: Kaggle Notebooks

If Colab GPU quota runs out, try Kaggle (also free GPU):

1. Go to [Kaggle](https://www.kaggle.com/)
2. Create notebook
3. Settings → Accelerator → GPU
4. Upload code and datasets
5. Run training

**Kaggle benefits:**
- 30 hrs/week GPU quota
- Persistent datasets
- Direct Kaggle dataset integration

---

## ✅ Pre-Flight Checklist

Before starting training on Colab:

- [ ] GPU enabled (Runtime → Change runtime type)
- [ ] Google Drive mounted
- [ ] Project files uploaded to Drive
- [ ] Datasets uploaded and verified
- [ ] `config.py` paths are correct
- [ ] All dependencies installed
- [ ] Sufficient Google Drive space (~5-10GB)

---

## 📞 Need Help?

**Common issues:**
1. GPU not available → Check runtime settings
2. Files not found → Verify Google Drive paths
3. Out of memory → Reduce batch size
4. Session timeout → Training auto-saves to Drive

**Documentation:**
- `TRAINING_GUIDE.md` - Complete training guide
- `VISUALIZATION_GUIDE.md` - All graphs explained
- `TRAINING_CHECKLIST.md` - Track progress

---

## 🎯 Quick Command Reference

```python
# Mount Drive
from google.colab import drive
drive.mount('/content/drive')

# Check GPU
import torch
print(torch.cuda.is_available())

# Navigate to project
%cd /content/drive/MyDrive/block-coding-robot

# Prepare datasets
!python prepare_datasets.py

# Train best model
!python train.py --experiment 2

# Validate
!python validate.py --model <path> --experiment 2

# Test
!python test.py --model <path> --image test.jpg --benchmark

# Download
from google.colab import files
files.download('path/to/file')
```

---

## 🎓 Summary

**With Google Colab:**
- ✅ Free GPU access (T4 with 16GB VRAM)
- ✅ ~4 hours total training time (vs 25+ hours on CPU)
- ✅ Auto-save to Google Drive
- ✅ Pre-installed Python & libraries
- ✅ No local setup needed

**Just upload your project and datasets, enable GPU, and run the notebook!**

---

**Ready to train? Open `LEGO_Detection_Training.ipynb` in Colab and start! 🚀**
