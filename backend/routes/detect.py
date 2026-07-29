from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List

from backend.services import detection, storage

router = APIRouter()


@router.get("/detect/status")
async def detect_status():
    """Report whether a trained model is available for detection."""
    return {"status": "success", "model_available": detection.model_available()}


class DropZone(BaseModel):
    left: float
    top: float
    right: float
    bottom: float


class DropZones(BaseModel):
    enabled: bool = True
    zones: List[DropZone] = []


@router.get("/detect/drop-zones")
async def get_drop_zones(project_name: str = "default"):
    """Return the user's saved drop-zone masks (exclusion ROI) for the Vision tab."""
    return {"status": "success", "drop_zones": storage.load_drop_zones(project_name)}


@router.put("/detect/drop-zones")
async def put_drop_zones(payload: DropZones, project_name: str = "default"):
    """Save the drop-zone masks drawn in the Vision tab. Coordinates are fractions
    of the frame (0..1); each zone is clamped and normalized so left<=right,
    top<=bottom before persisting."""
    zones = []
    for z in payload.zones:
        left, right = sorted((max(0.0, min(1.0, z.left)), max(0.0, min(1.0, z.right))))
        top, bottom = sorted((max(0.0, min(1.0, z.top)), max(0.0, min(1.0, z.bottom))))
        # Drop degenerate (zero-area) rectangles from stray clicks.
        if right - left < 0.01 or bottom - top < 0.01:
            continue
        zones.append({"left": left, "top": top, "right": right, "bottom": bottom})
    data = {"enabled": payload.enabled, "zones": zones}
    storage.save_drop_zones(data, project_name)
    return {"status": "success", "drop_zones": data}


@router.post("/detect")
async def detect_image(image: UploadFile = File(...), conf: float = 0.5):
    """Run LEGO detection on an uploaded image / webcam frame.

    Returns detections with bounding boxes, confidence, and target bins.
    """
    if not detection.model_available():
        raise HTTPException(
            503,
            "No trained model found. Place best.pt at models/lego_detector.pt",
        )

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(400, "Empty image upload")

    try:
        result = detection.detect(image_bytes, conf=conf)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Detection failed: {e}")

    return {"status": "success", **result}
