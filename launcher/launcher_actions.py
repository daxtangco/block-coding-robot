"""Side-effecting operations for the launcher.

Every operation streams subprocess output through a `log` callable so the
Tkinter diagnostics panel can show progress live. Nothing here imports tkinter.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from launcher.doctor import venv_python


def _stream(cmd, log) -> int:
    """Run cmd, pipe stdout+stderr line-by-line into log(str). Return exit code."""
    log(f"$ {' '.join(str(c) for c in cmd)}")
    proc = subprocess.Popen(
        [str(c) for c in cmd],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    for line in proc.stdout:
        log(line.rstrip("\n"))
    proc.wait()
    return proc.returncode


def find_system_python() -> str:
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
    _stream([str(py), "-m", "pip", "install", "--upgrade", "pip"], log)
    for req in req_files:
        code = _stream([str(py), "-m", "pip", "install", "-r", str(root / req)], log)
        if code != 0:
            log(f"ERROR: pip install -r {req} failed")
            return False
    return True
