"""Detection service: runs the trained YOLOv8 model on an image and maps
detections to sorting bins. Loads the model once (lazily) and reuses it.
"""

import sys
from pathlib import Path
from typing import Optional

# Project root is two levels up (backend/services/ -> project root).
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import get_model_path
from sorting_logic import LEGOSorter, Detection

_model = None          # cached YOLO instance
_model_path = None     # path the cache was built from
_sorter = LEGOSorter()


def model_available() -> bool:
    """True if a trained model can be located on disk."""
    return get_model_path() is not None


def reload():
    """Drop the cached model so the next request reloads from disk.

    Called after training swaps in a new models/lego_detector.pt, so /detect
    picks up the new weights without a server restart.
    """
    global _model, _model_path
    _model = None
    _model_path = None


def class_names() -> list:
    """Ordered class names of the active detection model (empty if none)."""
    if not model_available():
        return []
    try:
        model = _load_model()
        names = model.names  # {id: name} dict from ultralytics
        if isinstance(names, dict):
            return [names[k] for k in sorted(names, key=lambda x: int(x))]
        return list(names)
    except Exception:
        return []


def _load_model():
    """Load (and cache) the YOLO model. Raises if no model is present."""
    global _model, _model_path
    if _model is not None:
        return _model

    path = get_model_path()
    if path is None:
        raise FileNotFoundError(
            "No trained model found. Place best.pt at models/lego_detector.pt"
        )

    from ultralytics import YOLO  # imported lazily; heavy dependency
    _model = YOLO(str(path))
    _model_path = str(path)
    return _model


def warmup() -> bool:
    """Pre-load the model so the first real request isn't slow (~3.5s cold).
    Returns True if a model was loaded, False if none is available.
    """
    if not model_available():
        return False
    try:
        import numpy as np
        model = _load_model()
        model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)
        return True
    except Exception:
        return False


def detect(image_bytes: bytes, conf: float = 0.5) -> dict:
    """Run detection on a raw image and return detections + bin mapping.

    Args:
        image_bytes: encoded image (JPEG/PNG bytes), e.g. a webcam frame.
        conf: minimum confidence threshold.

    Returns a dict with detections, per-bin statistics, and the source model.
    """
    import cv2
    import numpy as np

    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Could not decode image data")

    model = _load_model()
    results = model(frame, conf=conf, verbose=False)

    detections = []
    detection_objs = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = result.names[class_id]
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())

            det = Detection(class_name=class_name, confidence=confidence,
                            bbox=(x1, y1, x2, y2))
            detection_objs.append(det)

            try:
                bin_name, bin_pos = _sorter.get_target_bin(class_name)
            except ValueError:
                bin_name, bin_pos = None, None

            detections.append({
                "class_name": class_name,
                "confidence": round(confidence, 4),
                "bbox": [x1, y1, x2, y2],
                "center": list(det.center),
                "target_bin": bin_name,
                "dropoff_position": list(bin_pos) if bin_pos else None,
            })

    bin_stats = _sorter.get_bin_statistics(detection_objs) if detection_objs else {}

    return {
        "count": len(detections),
        "detections": detections,
        "bin_statistics": bin_stats,
        "model_path": _model_path,
    }
