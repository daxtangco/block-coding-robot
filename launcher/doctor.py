"""Environment checks for the Block Robot launcher.

Single source of truth: every launcher button calls into these functions.
Pure logic — must NOT import tkinter, so it stays unit-testable.
"""
import sys
import platform
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
