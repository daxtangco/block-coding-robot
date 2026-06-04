from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from backend.services.storage import load_settings, load_poses
from backend.services.template_engine import fill_template
from backend.services.builder import compile_arduino, get_template_path

router = APIRouter()

class BuildRequest(BaseModel):
    generated_code: str = ""  # Optional - empty for manual mode
    target_board: str = "arm"  # "arm" or "vision"
    project_name: str = "default"
    use_pca9685: bool = True  # Use PCA9685 servo driver by default
    use_ap_mode: bool = False  # Use AP mode (WiFi access point) instead of Blynk

@router.post("/build")
async def build_firmware(request: BuildRequest):
    """
    Receives generated C++ code, fills template, compiles, returns .bin path.
    """
    # Load project data
    settings = load_settings(request.project_name)
    poses = load_poses(request.project_name)

    # Load template
    if request.target_board == "arm":
        # Use centralized template selection logic
        template_file = get_template_path(
            use_pca9685=request.use_pca9685,
            use_ap_mode=request.use_ap_mode
        )
    elif request.target_board == "vision":
        template_file = Path("backend/templates") / "vision_board.ino"
    else:
        raise HTTPException(400, "Invalid target_board. Must be 'arm' or 'vision'")

    if not template_file.exists():
        raise HTTPException(500, f"Template not found: {template_file}")

    template_content = template_file.read_text()

    # Fill template
    filled_sketch = fill_template(
        template_content,
        settings,
        poses,
        request.generated_code if request.generated_code else "// Manual mode only"
    )

    # Compile
    success, output, bin_path = await compile_arduino(filled_sketch)

    if not success:
        raise HTTPException(500, f"Compilation failed:\n{output}")

    return {
        "status": "success",
        "build_log": output,
        "download_url": f"/api/download/{bin_path.parent.name}",
        "build_id": bin_path.parent.name,
        "firmware_size": bin_path.stat().st_size
    }

@router.post("/build/manual")
async def build_manual_mode(project_name: str = "default"):
    """
    Quick build for manual control only (no generated code).
    """
    return await build_firmware(BuildRequest(
        generated_code="",
        target_board="arm",
        project_name=project_name,
        use_pca9685=True
    ))

@router.get("/download/{build_id}")
async def download_binary(build_id: str):
    """Serves compiled .bin file for download or Web Serial flashing."""
    bin_path = Path("builds") / build_id / "sketch.ino.bin"
    if not bin_path.exists():
        raise HTTPException(404, "Build not found or expired")
    return FileResponse(
        bin_path,
        media_type="application/octet-stream",
        filename=f"robot-firmware-{build_id[:8]}.bin",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*"
        }
    )
