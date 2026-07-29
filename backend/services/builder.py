import asyncio
import shutil
import sys
import uuid
import subprocess
from pathlib import Path
from typing import Tuple, Optional
from concurrent.futures import ThreadPoolExecutor

BUILDS_DIR = Path("builds")
BUILDS_DIR.mkdir(exist_ok=True)


def _arduino_cli() -> str:
    """Resolve the arduino-cli executable.

    The launcher installs a private copy into <project_root>/tools/ (NOT on the
    system PATH), so calling the bare name "arduino-cli" fails on machines where
    it isn't also globally installed (WinError 2 / "not found"). Resolve the same
    way the launcher's doctor does: a system copy on PATH wins, else our private
    tools/ copy. Falls back to the bare name so the "not found" error still reads
    sensibly if neither exists.
    """
    on_path = shutil.which("arduino-cli")
    if on_path:
        return on_path
    exe = "arduino-cli.exe" if sys.platform == "win32" else "arduino-cli"
    local = Path.cwd() / "tools" / exe   # matches launcher doctor.arduino_cli_local
    if local.exists():
        return str(local)
    return "arduino-cli"

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

def list_serial_ports() -> list:
    """Return connected serial ports via `arduino-cli board list`.

    Each entry: {port, protocol, label, fqbn?}. Type is "Unknown" for ESP32
    USB-UART bridges (they don't self-identify), so we list all serial ports.
    """
    try:
        result = subprocess.run(
            [_arduino_cli(), "board", "list", "--format", "json"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=30,
        )
    except Exception as e:
        return [{"error": str(e)}]

    import json
    ports = []
    try:
        data = json.loads(result.stdout)
        # arduino-cli 1.x: {"detected_ports": [{"port": {...}, "matching_boards": [...]}]}
        entries = data.get("detected_ports", data) if isinstance(data, dict) else data
        for entry in entries:
            port = entry.get("port", entry)
            if port.get("protocol") != "serial":
                continue
            boards = entry.get("matching_boards") or []
            ports.append({
                "port": port.get("address"),
                "protocol": port.get("protocol"),
                "label": port.get("label") or port.get("address"),
                "fqbn": boards[0]["fqbn"] if boards else None,
            })
    except (json.JSONDecodeError, KeyError, TypeError):
        return [{"error": "Could not parse board list", "raw": result.stdout[:500]}]
    return ports


async def compile_and_upload(
    sketch_content: str, port: str, board_fqbn: str = "esp32:esp32:esp32"
) -> Tuple[bool, str]:
    """Compile the sketch and flash it to the board on `port` in one step.

    Uses `arduino-cli compile --upload`, which recompiles fresh and writes to
    the chip — no chance of flashing a stale .bin.
    """
    build_id = str(uuid.uuid4())
    build_dir = BUILDS_DIR / build_id
    build_dir.mkdir()
    sketch_dir = build_dir / "sketch"
    sketch_dir.mkdir()
    (sketch_dir / "sketch.ino").write_text(sketch_content)

    cmd = [
        _arduino_cli(), "compile", "--upload",
        "--fqbn", board_fqbn,
        "--port", port,
        str(sketch_dir),
    ]
    try:
        loop = asyncio.get_event_loop()
        returncode, output = await loop.run_in_executor(
            _executor, _run_compile_sync, cmd, str(Path.cwd())
        )
        if returncode == 0:
            return True, output
        return False, f"Upload failed:\n{output}"
    except FileNotFoundError as e:
        return False, f"arduino-cli not found in PATH.\nError: {e}"
    except Exception as e:
        import traceback
        return False, f"Upload error: {e}\n\n{traceback.format_exc()}"


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
        _arduino_cli(), "compile",
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
