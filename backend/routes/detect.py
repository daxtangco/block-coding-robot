from fastapi import APIRouter, HTTPException, UploadFile, File

from backend.services import detection

router = APIRouter()


@router.get("/detect/status")
async def detect_status():
    """Report whether a trained model is available for detection."""
    return {"status": "success", "model_available": detection.model_available()}


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
