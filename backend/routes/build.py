from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from backend.services.storage import load_settings, load_poses
from backend.services.template_engine import fill_template
from backend.services.builder import compile_arduino

router = APIRouter()

class BuildRequest(BaseModel):
    generated_code: str
    target_board: str = "arm"  # "arm" or "vision"
    project_name: str = "default"

@router.post("/build")
async def build_firmware(request: BuildRequest):
    """
    Receives generated C++ code, fills template, compiles, returns .bin path.
    """
    # Load project data
    settings = load_settings(request.project_name)
    poses = load_poses(request.project_name)

    # Load template
    template_path = Path("backend/templates")
    if request.target_board == "arm":
        template_file = template_path / "arm_controller.ino"
    elif request.target_board == "vision":
        template_file = template_path / "vision_board.ino"
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
        request.generated_code
    )

    # Compile
    success, output, bin_path = await compile_arduino(filled_sketch)

    if not success:
        raise HTTPException(500, f"Compilation failed:\n{output}")

    return {
        "status": "success",
        "build_log": output,
        "download_url": f"/download/{bin_path.parent.name}",
        "build_id": bin_path.parent.name
    }

@router.get("/download/{build_id}")
async def download_binary(build_id: str):
    """Serves compiled .bin file."""
    bin_path = Path("builds") / build_id / "sketch.ino.bin"
    if not bin_path.exists():
        raise HTTPException(404, "Build not found or expired")
    return FileResponse(
        bin_path,
        media_type="application/octet-stream",
        filename=f"robot-firmware-{build_id[:8]}.bin"
    )
