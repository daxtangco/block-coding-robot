# ML Models Directory

This directory will contain the trained TensorFlow Lite models for object detection/classification.

## Current Status

**Vision firmware is using mock inference.** Real model integration happens during week 1 hardware testing.

## Expected Files

- `lego_classifier.tflite` - Quantized int8 model for lego sorting
- `model_data.h` - C array version of model for embedding in firmware

## Model Requirements

- **Input size**: 96×96 pixels (configurable)
- **Format**: TFLite int8 quantized
- **Size limit**: <200 KB (ESP32-CAM PSRAM constraint)
- **Classes**: red_small, blue_small, red_large, blue_large, none
- **Target accuracy**: >85% under demo lighting conditions

## Training Pipeline (Week 1)

1. **Dataset capture**: 50-100 images per class under final lighting
2. **Training**: MobileNet v2 with transfer learning
3. **Quantization**: Post-training int8 quantization
4. **Conversion**: TFLite → C header file
5. **Embedding**: Replace mock inference in `vision_board.ino`

## Converting TFLite to C Header

```bash
xxd -i lego_classifier.tflite > model_data.h
```

Then edit model_data.h to make the array name match expectations in firmware:
```cpp
const unsigned char model_data[] = { ... };
const unsigned int model_data_len = 123456;
```

## Integration Steps

1. Place `model_data.h` in same directory as `vision_board.ino`
2. Add `#include "model_data.h"` to firmware
3. Replace `mockInference()` with TFLite Micro inference code
4. Test accuracy with held-out test images before demo

## Notes

- Train model under **actual demo lighting**, not lab lighting
- Test model on physical hardware, not just on PC
- If accuracy <85%, capture more training data or adjust lighting
- Consider model size vs accuracy tradeoff for ESP32-CAM memory constraints
