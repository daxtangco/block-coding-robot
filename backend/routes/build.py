from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from backend.services.storage import load_settings, load_poses
from backend.services.template_engine import fill_template
from backend.services.builder import (
    compile_arduino, compile_and_upload, list_serial_ports, get_template_path,
)

router = APIRouter()

class BuildRequest(BaseModel):
    generated_code: str = ""  # Optional - empty for manual mode
    target_board: str = "arm"
    project_name: str = "default"

class UploadRequest(BaseModel):
    port: str
    generated_code: str = ""
    target_board: str = "arm"
    project_name: str = "default"


def _build_sketch(request: BuildRequest) -> str:
    """Load project data, select template, and fill it. Shared by build/upload."""
    settings = load_settings(request.project_name)
    poses = load_poses(request.project_name)

    if request.target_board != "arm":
        raise HTTPException(400, "Invalid target_board. Must be 'arm'")
    template_file = get_template_path()

    if not template_file.exists():
        raise HTTPException(500, f"Template not found: {template_file}")

    return fill_template(
        template_file.read_text(),
        settings,
        poses,
        request.generated_code if request.generated_code else "// Manual mode only",
    )

@router.post("/build")
async def build_firmware(request: BuildRequest):
    """
    Receives generated C++ code, fills template, compiles, returns .bin path.
    """
    filled_sketch = _build_sketch(request)

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


@router.get("/ports")
async def list_ports():
    """List connected serial ports for USB flashing."""
    return {"status": "success", "ports": list_serial_ports()}


@router.post("/upload")
async def upload_firmware(request: UploadRequest):
    """Compile and flash the firmware directly to the board over USB."""
    if not request.port:
        raise HTTPException(400, "No serial port specified")

    filled_sketch = _build_sketch(BuildRequest(
        generated_code=request.generated_code,
        target_board=request.target_board,
        project_name=request.project_name,
    ))

    success, output = await compile_and_upload(filled_sketch, request.port)
    if not success:
        raise HTTPException(500, output)

    return {"status": "success", "build_log": output, "port": request.port}

@router.post("/build/manual")
async def build_manual_mode(project_name: str = "default"):
    """
    Quick build for manual control only (no generated code).
    """
    return await build_firmware(BuildRequest(
        generated_code="",
        target_board="arm",
        project_name=project_name,
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
