"""Environment checks for the Block Robot launcher.

Single source of truth: every launcher button calls into these functions.
Pure logic — must NOT import tkinter, so it stays unit-testable.
"""
import sys
import platform
import shutil
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    status: str   # "ok" | "fail"
    label: str
    message: str
    fix_hint: str = ""


def venv_dir(project_root: Path) -> Path:
    return Path(project_root) / ".venv"


def venv_python(project_root: Path) -> Path:
    d = venv_dir(project_root)
    if sys.platform == "win32":
        return d / "Scripts" / "python.exe"
    return d / "bin" / "python"


def check_python(min_major: int = 3, min_minor: int = 8) -> CheckResult:
    v = sys.version_info
    label = "Python"
    ok = (v.major, v.minor) >= (min_major, min_minor)
    if ok:
        return CheckResult(
            "ok", label,
            f"Python {v.major}.{v.minor}.{v.micro} found",
        )
    return CheckResult(
        "fail", label,
        f"Python {min_major}.{min_minor}+ required (found {v.major}.{v.minor})",
        "Install Python from https://python.org, then click Re-check.",
    )


def check_venv(project_root: Path) -> CheckResult:
    py = venv_python(project_root)
    if py.exists():
        return CheckResult("ok", "Virtual env", "Project .venv ready")
    return CheckResult(
        "fail", "Virtual env",
        "No .venv yet",
        "Click Set up to create the project environment.",
    )


def check_deps_installed(project_root: Path, venv_py: Path, import_probe: str,
                         label: str, fix_hint: str) -> CheckResult:
    if not venv_py.exists():
        return CheckResult("fail", label, "No .venv yet", fix_hint)
    try:
        r = subprocess.run(
            [str(venv_py), "-c", f"import {import_probe}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return CheckResult("fail", label, f"{label} probe timed out (60 s)", fix_hint)
    except Exception as e:
        return CheckResult("fail", label, f"Could not probe: {e}", fix_hint)
    if r.returncode == 0:
        return CheckResult("ok", label, f"{label} installed")
    return CheckResult("fail", label, f"{label} missing", fix_hint)


def check_model(project_root: Path) -> CheckResult:
    m = Path(project_root) / "models" / "lego_detector.pt"
    if m.exists():
        return CheckResult("ok", "Model", "Model file present")
    return CheckResult(
        "fail", "Model", "lego_detector.pt not found",
        "Click Set up to download the model.",
    )


def check_tool_on_path(tool: str, label: str, fix_hint: str) -> CheckResult:
    if shutil.which(tool):
        return CheckResult("ok", label, f"{tool} found")
    return CheckResult("fail", label, f"{tool} not on PATH", fix_hint)


def check_arm_reachable(host: str = "192.168.4.1", port: int = 80,
                        timeout: float = 1.5) -> CheckResult:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return CheckResult("ok", "Arm", f"Arm reachable at {host}")
    except OSError:
        return CheckResult(
            "fail", "Arm", "Arm not reachable",
            f"Join the ROBOTARM-6654 WiFi, then click Re-check. "
            f"(Optional — only needed to drive the robot.)",
        )


WEB_FIX = "Click Set up to install the web dependencies."
VISION_FIX = "Click Set up to install the vision dependencies."
ARDUINO_FIX = ("Install arduino-cli and the esp32 core "
               "(see docs/ARDUINO_CLI_SETUP.md), then Re-check.")


def run_checks(project_root: Path, include_flash: bool = False) -> list:
    root = Path(project_root)
    py = venv_python(root)
    results = [
        check_python(),
        check_venv(root),
        check_deps_installed(root, py, "fastapi", "Web deps", WEB_FIX),
        check_deps_installed(root, py, "ultralytics", "Vision deps", VISION_FIX),
        check_model(root),
    ]
    if include_flash:
        results.append(check_tool_on_path("arduino-cli", "arduino-cli", ARDUINO_FIX))
        results.append(check_arm_reachable())
    return results


def all_ok(results: list) -> bool:
    return all(r.status == "ok" for r in results)


def first_failure(results: list):
    for r in results:
        if r.status == "fail":
            return r
    return None
