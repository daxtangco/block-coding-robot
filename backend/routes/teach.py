from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from backend.services import teachable

router = APIRouter()


@router.get("/teach/classes")
async def teach_classes(project_name: str = "default"):
    """List taught classes + example counts; whether a model is trained."""
    return {
        "status": "success",
        "classes": teachable.list_classes(project_name),
        "counts": teachable.class_counts(project_name),
        "trained": teachable.is_trained(project_name),
    }


@router.post("/teach/capture")
async def teach_capture(
    image: UploadFile = File(...),
    class_name: str = Form(...),
    project_name: str = Form("default"),
):
    """Capture one example image for a class."""
    data = await image.read()
    if not data:
        raise HTTPException(400, "Empty image upload")
    try:
        result = teachable.capture(project_name, class_name, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Capture failed: {e}")
    return {"status": "success", **result}


@router.post("/teach/train")
async def teach_train(project_name: str = Form("default")):
    """Train the classifier head on captured examples."""
    try:
        result = teachable.train(project_name)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Training failed: {e}")
    return {"status": "success", **result}


@router.post("/teach/classify")
async def teach_classify(
    image: UploadFile = File(...),
    project_name: str = Form("default"),
    conf: float = Form(0.5),
):
    """Classify an image against the trained model."""
    data = await image.read()
    if not data:
        raise HTTPException(400, "Empty image upload")
    try:
        result = teachable.classify(project_name, data, conf=conf)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Classify failed: {e}")
    return {"status": "success", **result}


@router.post("/teach/reset")
async def teach_reset(project_name: str = Form("default")):
    """Delete all captured data + classifier for a project."""
    return {"status": "success", **teachable.reset(project_name)}
