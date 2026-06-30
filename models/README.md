# ML Models Directory

This directory holds the trained object-detection model used for LEGO sorting.

## Drop-in model location

Place the trained PyTorch weights here so the inference scripts find them
automatically:

```
models/lego_detector.pt
```

`config.get_model_path()` resolves models in this order:

1. `models/lego_detector.pt` (this canonical location)
2. newest `training_output/models/*/stage2_finetuned/weights/best.pt`
3. newest `training_output/models/*/stage1_synthetic/weights/best.pt`

To deploy the model trained in Colab, download
`experiment_2_*/stage2_finetuned/weights/best.pt` from Google Drive and copy it
to `models/lego_detector.pt`.

## Model details

- **Architecture**: YOLOv8n (Ultralytics)
- **Classes (6)**: `brick_1x6`, `brick_2x2`, `brick_2x4`, `plate_1x2`, `plate_2x2`, `plate_2x4`
- **Input size**: 640×640
- **Validation (Colab run)**: mAP@0.5 ≈ 0.96, precision ≈ 0.90, recall ≈ 0.92

Class names and IDs are defined in `config.TARGET_CLASSES` (alphabetical order,
matching the IDs baked into the trained weights).

## Using the model

Run inference on a single image (auto-discovers the model):

```bash
python test.py --image datasets/images/00000.jpg --visualize
```

Run the full detection + sorting demo:

```bash
python integrated_sorting_demo.py
```

Validate against the local test split:

```bash
python validate.py --model models/lego_detector.pt --experiment 2
```

## Exported formats

`export_model.py` produces deployment formats alongside the `.pt` weights:

| Format | File | Size | Runs where |
|--------|------|------|-----------|
| PyTorch | `lego_detector.pt` | ~6 MB | host (training/inference) |
| ONNX | `lego_detector.onnx` | ~12 MB | host / cross-platform runtimes |
| TorchScript | `lego_detector.torchscript` | ~12 MB | host / C++ (libtorch) |
| TFLite (int8) | `lego_detector_int8.tflite` | ~3.2 MB | ESP32-CAM (see below) |

ONNX output tensor is `(1, 10, 8400)` = 4 bbox coords + 6 class scores, confirming
the 6-class model. ONNX was verified to load and run under `onnxruntime` locally.

### TFLite model details (built on Colab, verified here)

`lego_detector_int8.tflite` was exported with `--int8 --imgsz 160` and dropped
into this folder. Verified by parsing the flatbuffer directly (no TF runtime
needed):

- **Input**: `images` `[1, 160, 160, 3]` **float32**
- **Output**: `Identity` `[1, 10, 525]` float32 = 4 bbox coords + 6 class scores
  × 525 anchors (the 20²+10²+5² multi-scale grid at 160px)
- **Size**: 3.16 MB (weights int8-quantized; the I/O boundary is float32, which
  is Ultralytics/TF default int8-export behavior)

Note the **float32 I/O**: on-device code must feed the camera frame as float and
read float outputs — not the pure-int8 tensor path some ESP32 examples assume.
The 3.16 MB size exceeds typical ESP32-CAM internal flash budgets; deploying it
on-device needs a board/partition with PSRAM + a large app partition, or use the
host-streaming alternative below.

Regenerate ONNX + TorchScript locally (no TensorFlow needed):

```bash
python export_model.py --format onnx
python export_model.py --format torchscript
```

These require the ONNX chain only: `pip install onnx onnxslim onnxruntime`
(these have Python 3.14 wheels; TensorFlow does not — see the TFLite note below).

## ESP32-CAM deployment (TFLite)

The ESP32-CAM firmware (`backend/templates/vision_board.ino`) currently uses
`mockInference()`. The on-device model must be an **int8-quantized TFLite at a
small input size** — YOLOv8n at 640×640 float32 (~12 MB) will not fit the
ESP32-CAM (~4 MB flash / ~520 KB RAM).

### Why TFLite must be built on Colab (not locally)

The `pt → onnx → tf → tflite` chain needs TensorFlow, which has **no Python 3.14
wheels** (TF supports up to ~Python 3.12). This dev machine runs Python 3.14, so
TFLite export cannot run here. The training notebook
(`../LEGO_Detection_Training_v3.ipynb`) runs on Colab's Python 3.11 where
TensorFlow is available, so build the TFLite there.

### Colab procedure (produces the ESP32-ready model)

1. Run the notebook top-to-bottom (so `prepare_datasets.py` regenerates
   `training_output/prepared_datasets/experiment_2/data.yaml`, used for int8
   calibration — without it, accuracy drops).
2. After the clone cell, upload the local `export_model.py` and `config.py` into
   `/content/drive/MyDrive/block-coding-robot/` (the cloned GitHub copy predates
   the `--int8`/`--imgsz` flags and the 6-class config).
3. Edit the export cell to pass ESP32 flags:
   ```python
   !python export_model.py --model $exp2_model --format tflite --int8 --imgsz 160
   ```
   `--int8` = quantized (KB-scale); `--imgsz 160` = 160×160 input (bump to 320
   only if accuracy is too low and the board has PSRAM headroom).
4. Download the resulting `.tflite` from Drive into this `models/` folder.

### Flashing onto the board

1. Convert to a C header: `xxd -i lego_detector_int8.tflite > model_data.h`
2. Place `model_data.h` next to `vision_board.ino` and `#include` it
3. Replace `mockInference()` with TFLite Micro inference code

Alternative: run detection on the host PC (via the ONNX/TorchScript exports) and
stream results to the board, avoiding on-device TFLite Micro entirely.
