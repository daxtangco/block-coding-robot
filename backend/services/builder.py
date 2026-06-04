import asyncio
import uuid
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

BUILDS_DIR = Path("builds")
BUILDS_DIR.mkdir(exist_ok=True)

def get_template_path(use_pca9685: bool = True, use_ap_mode: bool = False) -> Path:
    """Get the appropriate firmware template path."""
    templates_dir = Path("backend/templates")

    if use_ap_mode:
        # AP mode template (always uses PCA9685)
        return templates_dir / "arm_controller_ap_mode.ino"
    elif use_pca9685:
        # PCA9685 template with Blynk (legacy)
        return templates_dir / "arm_controller_pca9685.ino"
    else:
        # Direct GPIO control (legacy)
        return templates_dir / "arm_controller.ino"

# Thread pool for running subprocess on Windows
_executor = ThreadPoolExecutor(max_workers=4)

def _run_compile_sync(cmd: list, cwd: str) -> Tuple[int, str]:
    """Run compilation synchronously in a thread (Windows-compatible)"""
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            text=True,
            timeout=300
        )
        return result.returncode, result.stdout
    except subprocess.TimeoutExpired:
        return -1, "Compilation timed out after 5 minutes. Try building again (cached cores speed up subsequent builds)."
    except Exception as e:
        import traceback
        return -1, f"Subprocess error: {str(e)}\n{traceback.format_exc()}"

async def compile_arduino(sketch_content: str, board_fqbn: str = "esp32:esp32:esp32") -> Tuple[bool, str, Optional[Path]]:
    """
    Compiles Arduino sketch using arduino-cli.
    Returns (success, output_log, binary_path).
    """
    build_id = str(uuid.uuid4())
    build_dir = BUILDS_DIR / build_id
    build_dir.mkdir()

    sketch_dir = build_dir / "sketch"
    sketch_dir.mkdir()
    sketch_file = sketch_dir / "sketch.ino"
    sketch_file.write_text(sketch_content)

    # Compile command
    cmd = [
        "arduino-cli", "compile",
        "--fqbn", board_fqbn,
        "--output-dir", str(build_dir),
        str(sketch_dir)
    ]

    try:
        # Run in thread pool to avoid Windows asyncio subprocess issues
        loop = asyncio.get_event_loop()
        returncode, output = await loop.run_in_executor(_executor, _run_compile_sync, cmd, str(Path.cwd()))

        if returncode == 0:
            # Find .bin file
            bin_file = build_dir / "sketch.ino.bin"
            if bin_file.exists():
                return True, output, bin_file
            else:
                return False, f"Build succeeded but .bin not found\n{output}", None
        else:
            return False, f"Compilation failed:\n{output}", None
    except FileNotFoundError as e:
        return False, f"arduino-cli not found in PATH. Please install and configure it (see docs/ARDUINO_CLI_SETUP.md)\nError: {str(e)}", None
    except Exception as e:
        import traceback
        error_detail = f"Build error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        return False, error_detail, None
