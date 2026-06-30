# Teachable Object Detection — Design

Lets students **teach the robot their own objects by example** inside the block-coding
IDE, then sort them — without dataset annotation, GPU, or Colab. Design only; not
yet implemented.

## Goal

A student can: name a class ("red gear"), show it to the webcam and capture a handful
of examples, click **Train**, and within seconds get a working `camera sees [red gear]`
block they can use to drive the arm. New classes also feed the sorting logic.

## Why not retrain YOLO

The existing YOLOv8 model does **object detection** (bounding boxes + class) and is the
right tool for the fixed 6-class LEGO set. But retraining it for user-defined objects
requires per-image box annotation, a GPU, and minutes of training on Colab — far too
heavy for a "teach my robot" button in a classroom. So Teachable mode trades capability
for speed and accessibility.

## Approach: frozen-backbone embeddings + tiny classifier

This is the Google Teachable Machine pattern: **decouple feature extraction from
classification.**

1. **Feature extraction (frozen, pretrained):** each captured frame is run once through
   a small pretrained CNN backbone (e.g. MobileNetV2) to produce a fixed-length
   embedding (~1024 floats). This backbone is never trained; it is a generic image
   "fingerprint" extractor. Cost: a few ms/image on CPU.
2. **Train only a tiny head:** fit a lightweight classifier (logistic regression /
   single dense layer) on the embeddings. With ~20 images × 3 classes this trains in
   **under a second** on CPU — no GPU, no Colab, no annotation.
3. **Inference:** new webcam frame → embedding → classifier → `{class, confidence}`,
   reusing the existing `/api/detect` response shape.

### Detection vs. classification — the key limitation

This classifies **the single dominant object in view**; it does not localize multiple
objects in a cluttered scene the way YOLO does. Implications to state explicitly in the
thesis:

- Best for a "present one object to the camera → sort it" station, not "dump 50 bricks
  and sort the pile."
- A **plain, consistent background** materially improves accuracy (embedding classifiers
  pick up background cues). Recommend a solid-color mat.
- The trained YOLO LEGO model remains available as a separate "pretrained mode"; Teachable
  mode is the "make your own" path. The contrast (fixed expert model vs. user-trained
  lightweight model) is itself a useful thesis discussion point.

## Where it runs: server-side via ONNX

The backbone runs as a **MobileNet ONNX model through `onnxruntime`** (already installed
and Python-3.14-safe — TensorFlow is not available on this Python). Keeps everything in
the existing FastAPI backend, no new browser dependencies, and reuses the current
request/response pattern. Trade-off vs. in-browser (TensorFlow.js): students share the
one laptop's CPU, but there is a single code path and no model download per device — fine
for a single-station setup.

## Student flow (UI)

A new **🎓 Teach Object** tab (mirrors the existing Vision tab layout):

1. **Add class** — type a name ("red gear"), click *Add Class*.
2. **Capture examples** — live webcam; click *Capture* ~15–20× while rotating the object.
   Thumbnails fill a strip. Repeat per object.
3. **Train** — click *Train Model*; a progress bar runs for a few seconds.
4. **Use** — taught classes immediately populate the `camera sees [▼]` block dropdown and
   the Vision tab. Student programs sorting with their own objects.

## How it maps onto the existing codebase

| Need | Reuse / add |
|------|-------------|
| Webcam capture + frame→JPEG | already in `frontend/js/ui/vision-panel.js` |
| Inference endpoint pattern | clone `backend/routes/detect.py` → `routes/teach.py` (capture, train, classify) |
| Model load + warmup pattern | mirror `backend/services/detection.py` → `services/teachable.py` |
| Dynamic block dropdown | `camera_sees` block reads a class list — point it at taught classes (served by an endpoint) |
| Per-project persistence | same `projects/<name>/` pattern as poses/settings — store embeddings + trained head + class names |
| Class → bin sorting | `LEGOSorter` already maps class→bin; extend to allow user-defined bins |

## Proposed components (when built)

- `backend/services/teachable.py` — load MobileNet ONNX (cached, warmed at startup like
  the detector); `embed(image)`, `train(project)`, `classify(project, image)`.
- `backend/routes/teach.py` —
  - `POST /api/teach/capture` (image + class name → store embedding)
  - `POST /api/teach/train` (fit classifier for a project)
  - `POST /api/teach/classify` (image → class + confidence)
  - `GET  /api/teach/classes` (list taught classes — feeds the block dropdown)
- `frontend/js/ui/teach-panel.js` + a **Teach Object** tab/workspace in `index.html`.
- Storage: `projects/<name>/teachable/` — `embeddings.npz`, `classifier.json`,
  `classes.json`.

## Persistence model

Store **embeddings**, not raw images (smaller, privacy-friendlier, and lets retraining be
instant). The trained classifier head serializes to a small JSON (weights + class names).
A project can be re-trained anytime by re-fitting on stored embeddings, or extended by
capturing more.

## Open questions to resolve before building

- **Min examples / class** before *Train* is allowed (suggest ≥10, warn below).
- **Confidence display + threshold** in blocks (reuse the Vision conf slider).
- **User-defined bins**: do students name bins too, or map taught classes onto the
  existing brick/plate bins?
- **Backbone choice & size**: MobileNetV2 (small, fast) vs. a slightly larger backbone for
  accuracy — measure on CPU.
- **"Unknown" handling**: reject low-confidence frames as "nothing" so the arm doesn't act
  on garbage.

## Status

Design only. No code written. Development is currently pinned; build is a separate,
sizable effort (new tab + capture/train/storage + dynamic blocks + a MobileNet ONNX
dependency).
