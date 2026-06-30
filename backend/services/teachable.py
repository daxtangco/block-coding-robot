"""Teachable-object service.

Lets users teach custom object classes by example (Teachable-Machine style):
a frozen MobileNetV2 backbone turns each webcam frame into a 1280-dim embedding,
and a tiny logistic-regression head is trained on those embeddings in <1s on CPU.

No dataset annotation, no GPU, no Colab. The backbone runs via onnxruntime
(Python-3.14-safe; TensorFlow is not available on this Python).

Per-project storage under projects/<name>/teachable/:
  - embeddings.npz   captured embeddings + integer labels
  - classifier.pkl   trained sklearn head
  - classes.json     class-name list (index = label id)
"""

import json
import pickle
import sys
import threading
from pathlib import Path
from typing import List, Optional

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# MobileNetV2 final feature map is 1280 channels; after global average pooling
# that is our embedding dimension.
EMBED_DIM = 1280
INPUT_SIZE = 224  # MobileNet's native input
MODELS_DIR = _ROOT / "models"
BACKBONE_ONNX = MODELS_DIR / "mobilenet_v2_backbone.onnx"

# ImageNet normalization (MobileNetV2 was trained with these).
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)

_session = None
_session_lock = threading.Lock()


def _export_backbone():
    """Export a frozen MobileNetV2 feature extractor (+ global pool) to ONNX.

    Done once; the resulting file is reused. Requires torch/torchvision, which
    are only needed for this one-time export, not for inference.
    """
    import torch
    import torch.nn as nn
    from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    weights = MobileNet_V2_Weights.IMAGENET1K_V1
    net = mobilenet_v2(weights=weights)

    # Keep convolutional features, then global-average-pool to (N, 1280).
    backbone = nn.Sequential(
        net.features,
        nn.AdaptiveAvgPool2d(1),
        nn.Flatten(),
    ).eval()

    dummy = torch.zeros(1, 3, INPUT_SIZE, INPUT_SIZE)
    torch.onnx.export(
        backbone, dummy, str(BACKBONE_ONNX),
        input_names=["input"], output_names=["embedding"],
        dynamic_axes={"input": {0: "batch"}, "embedding": {0: "batch"}},
        opset_version=18,
    )


def _get_session():
    """Load (and cache) the ONNX backbone inference session, exporting if needed."""
    global _session
    if _session is not None:
        return _session
    with _session_lock:
        if _session is not None:
            return _session
        if not BACKBONE_ONNX.exists():
            _export_backbone()
        import onnxruntime as ort
        _session = ort.InferenceSession(
            str(BACKBONE_ONNX), providers=["CPUExecutionProvider"]
        )
    return _session


def warmup() -> bool:
    """Pre-build/load the backbone so the first capture isn't slow."""
    try:
        sess = _get_session()
        sess.run(None, {"input": np.zeros((1, 3, INPUT_SIZE, INPUT_SIZE), np.float32)})
        return True
    except Exception:
        return False


def _preprocess(image_bytes: bytes) -> np.ndarray:
    """Decode image bytes -> normalized (1, 3, 224, 224) float32 tensor."""
    import cv2

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image data")
    frame = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    chw = np.transpose(frame, (2, 0, 1))  # HWC -> CHW
    chw = (chw - _MEAN) / _STD
    return chw[None, ...]  # add batch dim


def embed(image_bytes: bytes) -> np.ndarray:
    """Return the 1280-dim embedding for one image."""
    sess = _get_session()
    out = sess.run(None, {"input": _preprocess(image_bytes)})[0]
    return out[0].astype(np.float32)


# ---------------------------------------------------------------------------
# Per-project storage
# ---------------------------------------------------------------------------

def _project_dir(project_name: str) -> Path:
    d = _ROOT / "projects" / project_name / "teachable"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load_classes(project_name: str) -> List[str]:
    f = _project_dir(project_name) / "classes.json"
    return json.loads(f.read_text()) if f.exists() else []


def _save_classes(project_name: str, classes: List[str]):
    (_project_dir(project_name) / "classes.json").write_text(json.dumps(classes))


def _load_embeddings(project_name: str):
    f = _project_dir(project_name) / "embeddings.npz"
    if not f.exists():
        return np.empty((0, EMBED_DIM), np.float32), np.empty((0,), np.int64)
    data = np.load(f)
    return data["X"], data["y"]


def _save_embeddings(project_name: str, X: np.ndarray, y: np.ndarray):
    np.savez(_project_dir(project_name) / "embeddings.npz", X=X, y=y)


def list_classes(project_name: str = "default") -> List[str]:
    return _load_classes(project_name)


def class_counts(project_name: str = "default") -> dict:
    """Number of captured examples per class name."""
    classes = _load_classes(project_name)
    _, y = _load_embeddings(project_name)
    counts = {c: 0 for c in classes}
    for label in y:
        if 0 <= int(label) < len(classes):
            counts[classes[int(label)]] += 1
    return counts


def capture(project_name: str, class_name: str, image_bytes: bytes) -> dict:
    """Embed one example image and store it under the given class."""
    class_name = class_name.strip()
    if not class_name:
        raise ValueError("class_name is required")

    classes = _load_classes(project_name)
    if class_name not in classes:
        classes.append(class_name)
        _save_classes(project_name, classes)
    label = classes.index(class_name)

    vec = embed(image_bytes)
    X, y = _load_embeddings(project_name)
    X = np.vstack([X, vec[None, :]])
    y = np.concatenate([y, [label]])
    _save_embeddings(project_name, X, y)

    return {"class_name": class_name, "total_for_class": int((y == label).sum()),
            "total_examples": int(len(y))}


def train(project_name: str = "default", min_per_class: int = 5) -> dict:
    """Fit the logistic-regression head on stored embeddings."""
    from sklearn.linear_model import LogisticRegression

    classes = _load_classes(project_name)
    X, y = _load_embeddings(project_name)

    if len(classes) < 2:
        raise ValueError("Need at least 2 classes to train")
    counts = {c: int((y == i).sum()) for i, c in enumerate(classes)}
    thin = [c for c, n in counts.items() if n < min_per_class]
    if thin:
        raise ValueError(
            f"Each class needs >= {min_per_class} examples. Low: {thin}"
        )

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X, y)
    train_acc = float(clf.score(X, y))

    with open(_project_dir(project_name) / "classifier.pkl", "wb") as f:
        pickle.dump(clf, f)

    return {"classes": classes, "counts": counts,
            "examples": int(len(y)), "train_accuracy": round(train_acc, 4)}


def is_trained(project_name: str = "default") -> bool:
    return (_project_dir(project_name) / "classifier.pkl").exists()


def _load_classifier(project_name: str):
    f = _project_dir(project_name) / "classifier.pkl"
    if not f.exists():
        return None
    with open(f, "rb") as fh:
        return pickle.load(fh)


def classify(project_name: str, image_bytes: bytes, conf: float = 0.5) -> dict:
    """Classify one image using the trained head."""
    clf = _load_classifier(project_name)
    if clf is None:
        raise ValueError("No trained model for this project. Capture examples and train first.")

    classes = _load_classes(project_name)
    vec = embed(image_bytes)[None, :]
    probs = clf.predict_proba(vec)[0]
    best = int(np.argmax(probs))
    confidence = float(probs[best])

    class_name = classes[best] if confidence >= conf else None  # None = "unknown"
    return {
        "class_name": class_name,
        "confidence": round(confidence, 4),
        "raw_class": classes[best],
        "all_scores": {c: round(float(p), 4) for c, p in zip(classes, probs)},
    }


def reset(project_name: str = "default") -> dict:
    """Delete all captured data + classifier for a project."""
    d = _project_dir(project_name)
    for name in ("embeddings.npz", "classifier.pkl", "classes.json"):
        p = d / name
        if p.exists():
            p.unlink()
    return {"status": "reset"}
