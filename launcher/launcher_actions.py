"""Side-effecting operations for the launcher.

Every operation streams subprocess output through a `log` callable so the
Tkinter diagnostics panel can show progress live. Nothing here imports tkinter.
"""
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Optional

from launcher.doctor import venv_python
from launcher import doctor


def _stream(cmd, log) -> int:
    """Run cmd, pipe stdout+stderr line-by-line into log(str). Return exit code.

    A failure to spawn (e.g. executable not found) is reported through `log`
    and returned as exit code 127 rather than raised, so callers can rely on
    the return code for every failure mode.
    """
    log(f"$ {' '.join(str(c) for c in cmd)}")
    try:
        proc = subprocess.Popen(
            [str(c) for c in cmd],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
    except OSError as e:
        log(f"ERROR: could not run {cmd[0]}: {e}")
        return 127
    try:
        for line in proc.stdout:
            log(line.rstrip("\n"))
    finally:
        proc.stdout.close()
    proc.wait()
    return proc.returncode


def find_system_python() -> Optional[str]:
    """Find a real system Python 3.8+ (not the frozen launcher interpreter)."""
    candidates = ["python3", "python"]
    # When NOT frozen, the running interpreter is itself a valid choice.
    if not getattr(sys, "frozen", False):
        candidates.insert(0, sys.executable)
    for name in candidates:
        exe = name if os.path.isabs(name) else shutil.which(name)
        if not exe:
            continue
        try:
            r = subprocess.run(
                [exe, "-c",
                 "import sys; sys.exit(0 if sys.version_info[:2] >= (3,8) else 1)"],
                timeout=15,
            )
        except Exception:
            continue
        if r.returncode == 0:
            return exe
    return None


def create_venv(project_root: Path, system_python: str, log) -> bool:
    root = Path(project_root)
    code = _stream([system_python, "-m", "venv", str(root / ".venv")], log)
    if code != 0:
        log("ERROR: failed to create .venv")
        return False
    return True


def pip_install(project_root: Path, req_files, log) -> bool:
    root = Path(project_root)
    py = venv_python(root)
    if _stream([str(py), "-m", "pip", "install", "--upgrade", "pip"], log) != 0:
        log("WARNING: pip self-upgrade failed; continuing with existing pip")
    for req in req_files:
        code = _stream([str(py), "-m", "pip", "install", "-r", str(root / req)], log)
        if code != 0:
            log(f"ERROR: pip install -r {req} failed")
            return False
    return True


MODEL_URL = (
    "https://github.com/daxtangco/block-coding-robot/"
    "releases/latest/download/lego_detector.pt"
)


def download_model(project_root: Path, log, url: str = MODEL_URL) -> bool:
    root = Path(project_root)
    dest_dir = root / "models"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "lego_detector.pt"
    part = dest_dir / "lego_detector.pt.part"
    log(f"Downloading model from {url} …")
    try:
        urllib.request.urlretrieve(url, str(part))
    except Exception as e:
        log(f"ERROR: model download failed: {e}")
        log(f"Manual fallback: download {url} into {dest}")
        if part.exists():
            part.unlink()
        return False
    part.replace(dest)
    log("Model downloaded.")
    return True


def start_backend(project_root: Path, log) -> subprocess.Popen:
    root = Path(project_root)
    py = venv_python(root)
    log("Starting IDE server on http://localhost:8000 …")
    return subprocess.Popen(
        [str(py), str(root / "backend" / "main.py")],
        cwd=str(root),
    )


def flash_firmware(project_root: Path, port: str, sketch_path: Path, log) -> bool:
    sketch_dir = Path(sketch_path).parent
    cmd = [
        "arduino-cli", "compile", "--upload",
        "--fqbn", "esp32:esp32:esp32",
        "--port", port,
        str(sketch_dir),
    ]
    code = _stream(cmd, log)
    if code != 0:
        log("ERROR: flash failed")
        return False
    log("Flash complete.")
    return True


def run_setup(project_root: Path, log,
              req_files=("backend/requirements.txt", "requirements-vision.txt")) -> bool:
    root = Path(project_root)

    sys_py = find_system_python()
    if not sys_py:
        log("ERROR: No Python 3.8+ found. Install it from https://python.org, "
            "then click Set up again.")
        return False
    log(f"Using system Python: {sys_py}")

    if not venv_python(root).exists():
        if not create_venv(root, sys_py, log):
            return False
    else:
        log(".venv already exists — reusing it.")

    if not pip_install(root, list(req_files), log):
        return False

    if doctor.check_model(root).status == "ok":
        log("Model already present — skipping download.")
    else:
        if not download_model(root, log):
            return False

    log("✅ Setup complete.")
    return True
