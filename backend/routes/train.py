from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from backend.services import trainer, detection

router = APIRouter()


@router.post("/train/upload")
async def train_upload(
    dataset: UploadFile = File(...),
    project_name: str = Form("default"),
):
    """Upload + validate a YOLOv8-format dataset .zip for training."""
    data = await dataset.read()
    if not data:
        raise HTTPException(400, "Empty dataset upload")
    try:
        result = trainer.upload_dataset(project_name, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {e}")
    return {"status": "success", **result}


@router.post("/train/start")
async def train_start(
    project_name: str = Form("default"),
    epochs: int = Form(20),
    imgsz: int = Form(640),
):
    """Begin training on the uploaded dataset (runs in the background)."""
    try:
        result = trainer.start_training(project_name, epochs=epochs, imgsz=imgsz)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Could not start training: {e}")
    return {"status": "success", **result}


@router.get("/train/status")
async def train_status():
    """Poll current training progress."""
    return {"status": "success", **trainer.get_status()}


@router.get("/train/classes")
async def train_classes(project_name: str = "default"):
    """Class names available for the camera-sees block.

    Prefers the active detection model's classes (what /detect actually
    returns); falls back to the uploaded dataset's classes before training.
    """
    classes = detection.class_names() or trainer.get_classes(project_name)
    return {"status": "success", "classes": classes}
