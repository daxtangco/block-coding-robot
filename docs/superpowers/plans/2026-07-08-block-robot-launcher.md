# Block Robot Launcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one double-clickable, PyInstaller-frozen Tkinter app per OS (Windows/macOS/Linux) that guides a teacher from "downloaded a file" to "IDE running in the browser" with no terminal.

**Architecture:** A pure-logic `doctor.py` runs an ordered list of environment checks and is the single source of truth. `launcher_actions.py` performs the side-effecting operations (create `.venv`, pip install, download model, spawn uvicorn, flash via arduino-cli). `launcher.py` is a thin Tkinter view (layout B: buttons left, always-on diagnostics panel right) that wires buttons to the doctor and streams subprocess output into the panel. PyInstaller specs + a GitHub Actions matrix in `packaging/` produce the three release artifacts.

**Tech Stack:** Python 3.8+ stdlib (Tkinter, subprocess, venv, urllib, socket, shutil, pathlib), PyInstaller, GitHub Actions, pytest.

## Global Constraints

- Python floor: **3.8+** (matches existing `setup_environment.py:16` check).
- The frozen launcher bundles its own Python; the IDE runs from a **dedicated `.venv`** built from the teacher's *system* Python — never `--user`, never global.
- `.venv` interpreter path: `.venv/Scripts/python.exe` (Windows), `.venv/bin/python` (macOS/Linux).
- The **only** machine-mutating operation is **Set up** (creates `.venv`, installs both dep sets, downloads model). All other red checks are guide-only + Re-check.
- Model canonical deploy path: `models/lego_detector.pt` (from `config.py:43`).
- Backend start: run `backend/main.py` as a script with the `.venv` interpreter — it self-serves via `uvicorn.run(app, host="0.0.0.0", port=8000)` at `backend/main.py:87`.
- Dep files reused verbatim: `backend/requirements.txt` (web) and `requirements-vision.txt` (vision).
- Directory name for build tooling is **`packaging/`**, NOT `build/` (which is gitignored at `.gitignore:10`).
- `doctor.py` must NOT import Tkinter (keeps it unit-testable).
- All paths via `pathlib`; OS branches via `sys.platform` / `platform.system()`.
- The model Release asset URL is a single constant in `launcher_actions.py`; the repo is `https://github.com/daxtangco/block-coding-robot`.

---

### Task 1: Doctor check primitives + Python/venv checks

**Files:**
- Create: `launcher/doctor.py`
- Test: `tests/launcher/test_doctor.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces:
  - `CheckResult` dataclass: `status: str` (`"ok"` | `"fail"`), `label: str`, `message: str`, `fix_hint: str`.
  - `venv_dir(project_root: Path) -> Path` → `project_root / ".venv"`.
  - `venv_python(project_root: Path) -> Path` → the interpreter path inside `.venv` (OS-branched).
  - `check_python(min_major=3, min_minor=8) -> CheckResult`.
  - `check_venv(project_root: Path) -> CheckResult`.

- [ ] **Step 1: Write the failing test**

```python
# tests/launcher/test_doctor.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import doctor


def test_check_python_ok_on_current_interpreter():
    r = doctor.check_python(min_major=3, min_minor=8)
    assert r.status == "ok"
    assert "Python" in r.message


def test_check_python_fail_when_floor_too_high():
    r = doctor.check_python(min_major=99, min_minor=0)
    assert r.status == "fail"
    assert "python.org" in r.fix_hint


def test_venv_python_path_is_os_correct(tmp_path):
    p = doctor.venv_python(tmp_path)
    if sys.platform == "win32":
        assert p == tmp_path / ".venv" / "Scripts" / "python.exe"
    else:
        assert p == tmp_path / ".venv" / "bin" / "python"


def test_check_venv_fail_when_missing(tmp_path):
    r = doctor.check_venv(tmp_path)
    assert r.status == "fail"


def test_check_venv_ok_when_interpreter_present(tmp_path):
    py = doctor.venv_python(tmp_path)
    py.parent.mkdir(parents=True)
    py.write_text("")
    r = doctor.check_venv(tmp_path)
    assert r.status == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/launcher/test_doctor.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'launcher'`.

- [ ] **Step 3: Write minimal implementation**

```python
# launcher/doctor.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/launcher/test_doctor.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add launcher/doctor.py tests/launcher/test_doctor.py
git commit -m "feat(launcher): add doctor check primitives + python/venv checks"
```

---

### Task 2: Dependency, model, and tool checks in the doctor

**Files:**
- Modify: `launcher/doctor.py`
- Test: `tests/launcher/test_doctor_deps.py`

**Interfaces:**
- Consumes: `CheckResult`, `venv_python` from Task 1.
- Produces:
  - `check_deps_installed(project_root, venv_py, import_probe: str, label: str, fix_hint: str) -> CheckResult` — runs `venv_py -c "import <probe>"` and maps exit code to status.
  - `check_model(project_root: Path) -> CheckResult` — looks for `models/lego_detector.pt`.
  - `check_tool_on_path(tool: str, label: str, fix_hint: str) -> CheckResult` — wraps `shutil.which`.
  - `check_arm_reachable(host="192.168.4.1", port=80, timeout=1.5) -> CheckResult` — TCP connect probe; failure is non-blocking (still `status="fail"` but callers treat arm as optional).

- [ ] **Step 1: Write the failing test**

```python
# tests/launcher/test_doctor_deps.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import doctor


def test_check_model_fail_when_absent(tmp_path):
    r = doctor.check_model(tmp_path)
    assert r.status == "fail"


def test_check_model_ok_when_present(tmp_path):
    m = tmp_path / "models" / "lego_detector.pt"
    m.parent.mkdir(parents=True)
    m.write_bytes(b"fake")
    r = doctor.check_model(tmp_path)
    assert r.status == "ok"


def test_check_tool_on_path_ok_for_python():
    # sys.executable's dir has "python"; use a tool guaranteed present.
    name = "python" if sys.platform == "win32" else "sh"
    r = doctor.check_tool_on_path(name, "Tool", "install it")
    assert r.status == "ok"


def test_check_tool_on_path_fail_for_missing():
    r = doctor.check_tool_on_path("definitely-not-a-real-tool-xyz", "Tool", "install it")
    assert r.status == "fail"
    assert r.fix_hint == "install it"


def test_check_arm_reachable_fail_on_closed_port():
    # Port 1 on localhost is virtually never open.
    r = doctor.check_arm_reachable(host="127.0.0.1", port=1, timeout=0.2)
    assert r.status == "fail"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/launcher/test_doctor_deps.py -v`
Expected: FAIL — `AttributeError: module 'launcher.doctor' has no attribute 'check_model'`.

- [ ] **Step 3: Write minimal implementation**

Append to `launcher/doctor.py`:

```python
import shutil
import socket
import subprocess


def check_deps_installed(project_root: Path, venv_py: Path, import_probe: str,
                         label: str, fix_hint: str) -> CheckResult:
    if not venv_py.exists():
        return CheckResult("fail", label, "No .venv yet", fix_hint)
    try:
        r = subprocess.run(
            [str(venv_py), "-c", f"import {import_probe}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60,
        )
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/launcher/test_doctor_deps.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add launcher/doctor.py tests/launcher/test_doctor_deps.py
git commit -m "feat(launcher): add deps/model/tool/arm checks to doctor"
```

---

### Task 3: Doctor orchestration — ordered check runner

**Files:**
- Modify: `launcher/doctor.py`
- Test: `tests/launcher/test_doctor_runner.py`

**Interfaces:**
- Consumes: all checks from Tasks 1–2.
- Produces:
  - `run_checks(project_root: Path, include_flash: bool = False) -> list[CheckResult]` — runs checks 1–5 in order; if `include_flash`, appends arduino-cli (#6) and arm (#7). Returns the ordered list.
  - `all_ok(results: list[CheckResult]) -> bool`.
  - `first_failure(results: list[CheckResult]) -> CheckResult | None`.

- [ ] **Step 1: Write the failing test**

```python
# tests/launcher/test_doctor_runner.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import doctor


def test_run_checks_core_order(tmp_path):
    results = doctor.run_checks(tmp_path, include_flash=False)
    labels = [r.label for r in results]
    assert labels == ["Python", "Virtual env", "Web deps", "Vision deps", "Model"]


def test_run_checks_includes_flash(tmp_path):
    results = doctor.run_checks(tmp_path, include_flash=True)
    labels = [r.label for r in results]
    assert labels[-2:] == ["arduino-cli", "Arm"]


def test_all_ok_and_first_failure():
    good = [doctor.CheckResult("ok", "A", "x")]
    bad = [doctor.CheckResult("ok", "A", "x"),
           doctor.CheckResult("fail", "B", "y")]
    assert doctor.all_ok(good) is True
    assert doctor.all_ok(bad) is False
    assert doctor.first_failure(good) is None
    assert doctor.first_failure(bad).label == "B"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/launcher/test_doctor_runner.py -v`
Expected: FAIL — `AttributeError: ... has no attribute 'run_checks'`.

- [ ] **Step 3: Write minimal implementation**

Append to `launcher/doctor.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/launcher/test_doctor_runner.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add launcher/doctor.py tests/launcher/test_doctor_runner.py
git commit -m "feat(launcher): add ordered check runner to doctor"
```

---

### Task 4: Actions — venv creation + dependency install

**Files:**
- Create: `launcher/launcher_actions.py`
- Test: `tests/launcher/test_actions_setup.py`

**Interfaces:**
- Consumes: `doctor.venv_dir`, `doctor.venv_python`.
- Produces:
  - `find_system_python() -> str | None` — returns a system Python 3.8+ executable (NOT the frozen launcher's `sys.executable`); searches `python3`/`python` on PATH via `shutil.which` and verifies version.
  - `create_venv(project_root: Path, system_python: str, log) -> bool` — runs `system_python -m venv .venv`; `log` is a `callable(str)` sink.
  - `pip_install(project_root: Path, req_files: list[str], log) -> bool` — runs `venv_python -m pip install -r <each>`.
  - All streaming: each spawns via `_stream(cmd, log)` helper that pipes stdout line-by-line into `log`.

- [ ] **Step 1: Write the failing test**

```python
# tests/launcher/test_actions_setup.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import launcher_actions as la


def test_find_system_python_returns_valid_interpreter():
    py = la.find_system_python()
    assert py is not None
    assert isinstance(py, str) and len(py) > 0


def test_stream_captures_output():
    lines = []
    code = la._stream([sys.executable, "-c", "print('hello-stream')"], lines.append)
    assert code == 0
    assert any("hello-stream" in ln for ln in lines)


def test_stream_reports_nonzero_exit():
    lines = []
    code = la._stream([sys.executable, "-c", "import sys; sys.exit(3)"], lines.append)
    assert code == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/launcher/test_actions_setup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'launcher.launcher_actions'`.

- [ ] **Step 3: Write minimal implementation**

```python
# launcher/launcher_actions.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/launcher/test_actions_setup.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add launcher/launcher_actions.py tests/launcher/test_actions_setup.py
git commit -m "feat(launcher): add venv creation + pip install actions"
```

---

### Task 5: Actions — model download + backend/flash spawn

**Files:**
- Modify: `launcher/launcher_actions.py`
- Test: `tests/launcher/test_actions_run.py`

**Interfaces:**
- Consumes: `_stream`, `venv_python` from Task 4.
- Produces:
  - `MODEL_URL: str` — the GitHub Release asset URL constant.
  - `download_model(project_root: Path, log, url: str = MODEL_URL) -> bool` — downloads to `models/lego_detector.pt` via `urllib.request`, atomic-renames from a `.part` temp file.
  - `start_backend(project_root: Path, log) -> subprocess.Popen` — spawns `venv_python backend/main.py` with cwd=project_root, returns the handle (caller opens browser).
  - `flash_firmware(project_root: Path, port: str, sketch_path: Path, log) -> bool` — runs `arduino-cli compile --upload --fqbn esp32:esp32:esp32 --port <port> <sketch_dir>` (mirrors `backend/services/builder.py:98-103`).

- [ ] **Step 1: Write the failing test**

```python
# tests/launcher/test_actions_run.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import launcher_actions as la


def test_download_model_writes_file(tmp_path, monkeypatch):
    def fake_urlretrieve(url, filename):
        Path(filename).write_bytes(b"MODELBYTES")
    monkeypatch.setattr(la.urllib.request, "urlretrieve", fake_urlretrieve)

    ok = la.download_model(tmp_path, log=lambda s: None, url="http://x/model.pt")
    assert ok is True
    assert (tmp_path / "models" / "lego_detector.pt").read_bytes() == b"MODELBYTES"


def test_download_model_reports_failure(tmp_path, monkeypatch):
    def boom(url, filename):
        raise OSError("network down")
    monkeypatch.setattr(la.urllib.request, "urlretrieve", boom)

    logs = []
    ok = la.download_model(tmp_path, log=logs.append, url="http://x/model.pt")
    assert ok is False
    assert any("network down" in ln for ln in logs)
    # No partial file left behind.
    assert not (tmp_path / "models" / "lego_detector.pt").exists()


def test_model_url_is_defined():
    assert isinstance(la.MODEL_URL, str)
    assert la.MODEL_URL.startswith("http")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/launcher/test_actions_run.py -v`
Expected: FAIL — `AttributeError: module 'launcher.launcher_actions' has no attribute 'download_model'`.

- [ ] **Step 3: Write minimal implementation**

Add `import urllib.request` to the imports of `launcher/launcher_actions.py`, then append:

```python
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


def start_backend(project_root: Path, log):
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/launcher/test_actions_run.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add launcher/launcher_actions.py tests/launcher/test_actions_run.py
git commit -m "feat(launcher): add model download + backend/flash spawn actions"
```

---

### Task 6: Setup orchestration — the one auto-fix path

**Files:**
- Modify: `launcher/launcher_actions.py`
- Test: `tests/launcher/test_actions_orchestrate.py`

**Interfaces:**
- Consumes: `find_system_python`, `create_venv`, `pip_install`, `download_model` from Tasks 4–5; `doctor.check_model`.
- Produces:
  - `run_setup(project_root: Path, log, req_files=("backend/requirements.txt", "requirements-vision.txt")) -> bool` — the single machine-mutating routine: find system Python → create `.venv` (skip if present) → pip install both req sets → download model (skip if already present). Returns overall success. Each sub-step logs and short-circuits on failure.

- [ ] **Step 1: Write the failing test**

```python
# tests/launcher/test_actions_orchestrate.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import launcher_actions as la


def test_run_setup_happy_path(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(la, "find_system_python", lambda: "python3")
    monkeypatch.setattr(la, "create_venv", lambda root, py, log: calls.append("venv") or True)
    monkeypatch.setattr(la, "pip_install", lambda root, reqs, log: calls.append(("pip", tuple(reqs))) or True)
    monkeypatch.setattr(la, "download_model", lambda root, log, **k: calls.append("model") or True)

    ok = la.run_setup(tmp_path, log=lambda s: None)
    assert ok is True
    assert "venv" in calls and "model" in calls


def test_run_setup_aborts_when_no_python(tmp_path, monkeypatch):
    monkeypatch.setattr(la, "find_system_python", lambda: None)
    logs = []
    ok = la.run_setup(tmp_path, log=logs.append)
    assert ok is False
    assert any("Python" in ln for ln in logs)


def test_run_setup_skips_model_download_when_present(tmp_path, monkeypatch):
    m = tmp_path / "models" / "lego_detector.pt"
    m.parent.mkdir(parents=True)
    m.write_bytes(b"x")
    monkeypatch.setattr(la, "find_system_python", lambda: "python3")
    monkeypatch.setattr(la, "create_venv", lambda *a, **k: True)
    monkeypatch.setattr(la, "pip_install", lambda *a, **k: True)
    called = {"model": False}
    monkeypatch.setattr(la, "download_model", lambda *a, **k: called.__setitem__("model", True) or True)

    ok = la.run_setup(tmp_path, log=lambda s: None)
    assert ok is True
    assert called["model"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/launcher/test_actions_orchestrate.py -v`
Expected: FAIL — `AttributeError: ... has no attribute 'run_setup'`.

- [ ] **Step 3: Write minimal implementation**

Append to `launcher/launcher_actions.py` (add `from launcher import doctor` to imports):

```python
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
```

Also ensure the top-of-file imports include:

```python
from launcher.doctor import venv_python
from launcher import doctor
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/launcher/test_actions_orchestrate.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add launcher/launcher_actions.py tests/launcher/test_actions_orchestrate.py
git commit -m "feat(launcher): add run_setup orchestration (single auto-fix path)"
```

---

### Task 7: Tkinter window (layout B) wiring buttons to doctor + actions

**Files:**
- Create: `launcher/launcher.py`
- Create: `launcher/__init__.py` (empty package marker)
- Create: `tests/launcher/__init__.py` (empty)
- Test: manual smoke (Tkinter view is intentionally thin; logic is covered by Tasks 1–6).

**Interfaces:**
- Consumes: `doctor.run_checks/all_ok/first_failure`, `launcher_actions.run_setup/start_backend`.
- Produces: `main()` entrypoint; `class LauncherApp`.

- [ ] **Step 1: Create the package markers**

```bash
# launcher/__init__.py and tests/launcher/__init__.py are empty files
```

Create empty `launcher/__init__.py` and `tests/launcher/__init__.py`.

- [ ] **Step 2: Write the Tkinter view**

```python
# launcher/launcher.py
"""Block Robot launcher window (layout B: buttons left, live diagnostics right).

Thin view: all logic lives in doctor.py and launcher_actions.py. Long-running
actions run on a worker thread and stream into the diagnostics panel via a
thread-safe queue polled on the Tk main loop.
"""
import queue
import sys
import threading
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import scrolledtext

from launcher import doctor, launcher_actions as actions


def project_root() -> Path:
    # When frozen, resources sit beside the executable; else repo root (../).
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.proj = project_root()
        self.q: "queue.Queue[str]" = queue.Queue()
        self.backend_proc = None

        root.title("Block Robot IDE")
        root.geometry("720x360")

        header = tk.Label(root, text="🤖 Block Robot IDE",
                          font=("Segoe UI", 16, "bold"))
        header.pack(pady=6)

        body = tk.Frame(root)
        body.pack(fill="both", expand=True, padx=10, pady=6)

        btns = tk.Frame(body)
        btns.pack(side="left", fill="y", padx=(0, 10))
        self._btn(btns, "▶ Start IDE", self.on_start)
        self._btn(btns, "⚙️ Set up / update", self.on_setup)
        self._btn(btns, "🩺 Check my system", self.on_check)

        self.log = scrolledtext.ScrolledText(body, width=52, height=16,
                                             bg="#020617", fg="#e2e8f0",
                                             font=("Consolas", 9))
        self.log.pack(side="right", fill="both", expand=True)

        self.root.after(100, self._drain)
        self.on_check()

    def _btn(self, parent, text, cmd):
        b = tk.Button(parent, text=text, command=cmd, width=18, height=2)
        b.pack(pady=4)
        return b

    # ---- logging plumbing ----
    def _log(self, msg: str):
        self.q.put(msg)

    def _drain(self):
        try:
            while True:
                line = self.q.get_nowait()
                self.log.insert("end", line + "\n")
                self.log.see("end")
        except queue.Empty:
            pass
        self.root.after(100, self._drain)

    def _run_bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    # ---- button handlers ----
    def on_check(self):
        self._log("── Checking system ──")
        for r in doctor.run_checks(self.proj, include_flash=False):
            icon = "✅" if r.status == "ok" else "❌"
            self._log(f"{icon} {r.label}: {r.message}")
            if r.status == "fail" and r.fix_hint:
                self._log(f"   → {r.fix_hint}")

    def on_setup(self):
        def work():
            actions.run_setup(self.proj, self._log)
            self.on_check()
        self._run_bg(work)

    def on_start(self):
        results = doctor.run_checks(self.proj, include_flash=False)
        if not doctor.all_ok(results):
            fail = doctor.first_failure(results)
            self._log(f"❌ Can't start yet: {fail.label} — {fail.fix_hint}")
            return
        if self.backend_proc and self.backend_proc.poll() is None:
            self._log("IDE already running.")
        else:
            self.backend_proc = actions.start_backend(self.proj, self._log)
        webbrowser.open("http://localhost:8000")


def main():
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Manual smoke test**

Run: `python -m launcher.launcher`
Expected: a 720x360 window opens; the diagnostics panel auto-runs checks on launch and shows ✅/❌ rows; clicking **Check my system** re-runs them; clicking **Set up** streams pip output. (Flash button is added in Task 9.)

- [ ] **Step 4: Commit**

```bash
git add launcher/__init__.py launcher/launcher.py tests/launcher/__init__.py
git commit -m "feat(launcher): add Tkinter window wiring buttons to doctor + actions"
```

---

### Task 8: pytest config so tests import the package cleanly

**Files:**
- Create: `pytest.ini`
- Test: run the full suite.

**Interfaces:**
- Consumes: all test files from Tasks 1–6.
- Produces: repo-root import path for `launcher` package during tests.

- [ ] **Step 1: Write the config**

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -q
```

- [ ] **Step 2: Run the full launcher suite**

Run: `python -m pytest tests/launcher -v`
Expected: PASS — all tests from Tasks 1–6 green (19 passed).

- [ ] **Step 3: Commit**

```bash
git add pytest.ini
git commit -m "test(launcher): add pytest config for package imports"
```

---

### Task 9: Flash button + firmware picker

**Files:**
- Modify: `launcher/launcher.py`
- Test: manual smoke.

**Interfaces:**
- Consumes: `doctor.run_checks(include_flash=True)`, `builder.list_serial_ports` (reused from `backend/services/builder.py:46`), `actions.flash_firmware`.
- Produces: `on_flash` handler; a fourth button.

- [ ] **Step 1: Add the Flash button and handler**

In `LauncherApp.__init__`, after the "Check my system" button:

```python
        self._btn(btns, "🔨 Flash the robot", self.on_flash)
```

Add import near the top of `launcher/launcher.py`:

```python
from tkinter import messagebox
```

Add the handler method to `LauncherApp`:

```python
    def on_flash(self):
        results = doctor.run_checks(self.proj, include_flash=True)
        # arduino-cli (index 5) is required; arm (index 6) is optional.
        arduino = results[5]
        if arduino.status != "ok":
            self._log(f"❌ {arduino.label}: {arduino.fix_hint}")
            return

        sys.path.insert(0, str(self.proj))
        from backend.services.builder import list_serial_ports, get_template_path

        ports = [p for p in list_serial_ports() if p.get("port")]
        if not ports:
            self._log("❌ No serial port found. Plug in the ESP32 over USB, then Re-check.")
            return
        port = ports[0]["port"]
        sketch = get_template_path(use_ap_mode=True)
        self._log(f"Flashing {sketch.name} to {port} …")

        def work():
            actions.flash_firmware(self.proj, port, sketch, self._log)
        self._run_bg(work)
```

- [ ] **Step 2: Manual smoke test**

Run: `python -m launcher.launcher`
Expected: a fourth **🔨 Flash the robot** button appears. With no board plugged in, clicking it logs either the arduino-cli fix hint or "No serial port found". (Full flash requires hardware — verify the guard paths without a board.)

- [ ] **Step 3: Commit**

```bash
git add launcher/launcher.py
git commit -m "feat(launcher): add Flash button reusing builder serial-port + template logic"
```

---

### Task 10: PyInstaller specs + GitHub Actions release matrix

**Files:**
- Create: `packaging/launcher.spec`
- Create: `packaging/README.md`
- Create: `.github/workflows/release-launcher.yml`
- Test: local one-OS build + CI dry validation.

**Interfaces:**
- Consumes: `launcher/launcher.py` entrypoint (`launcher.main`).
- Produces: three release artifacts (`.exe`, `.app`/dmg-less folder, Linux binary) attached to a GitHub Release on tag push.

- [ ] **Step 1: Write the PyInstaller spec**

```python
# packaging/launcher.spec
# Build: pyinstaller packaging/launcher.spec
# Produces a one-file frozen launcher that bundles Python + Tkinter.
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['../launcher/launcher.py'],
    pathex=['..'],
    binaries=[],
    datas=[],
    hiddenimports=collect_submodules('launcher'),
    hookspath=[],
    runtime_hooks=[],
    excludes=['torch', 'ultralytics', 'cv2'],  # heavy IDE deps live in .venv, not here
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='Block-Robot',
    console=False,
    onefile=True,
)
```

- [ ] **Step 2: Write the packaging note**

```markdown
# packaging/

PyInstaller build for the Block Robot launcher.

Local build (current OS only):

    pip install pyinstaller
    pyinstaller packaging/launcher.spec

Output: `dist/Block-Robot` (or `Block-Robot.exe` on Windows).

The frozen launcher bundles its own Python + Tkinter. It does NOT bundle the
IDE's heavy deps (torch/ultralytics/opencv) — those install into the project
`.venv` when the teacher clicks **Set up**.

CI builds all three OS artifacts and attaches them to the GitHub Release
(see `.github/workflows/release-launcher.yml`).
```

- [ ] **Step 3: Write the release workflow**

```yaml
# .github/workflows/release-launcher.yml
name: Release Launcher
on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Tk (Linux)
        if: runner.os == 'Linux'
        run: sudo apt-get update && sudo apt-get install -y python3-tk
      - name: Install PyInstaller
        run: pip install pyinstaller
      - name: Build
        run: pyinstaller packaging/launcher.spec
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: launcher-${{ matrix.os }}
          path: dist/*

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          path: artifacts
      - name: Attach to release
        uses: softprops/action-gh-release@v2
        with:
          files: artifacts/**/*
```

- [ ] **Step 4: Local build validation (current OS)**

Run: `pip install pyinstaller && pyinstaller packaging/launcher.spec`
Expected: build succeeds; `dist/Block-Robot` (or `.exe`) exists and launches the window when double-clicked / run.

- [ ] **Step 5: Commit**

```bash
git add packaging/launcher.spec packaging/README.md .github/workflows/release-launcher.yml
git commit -m "build(launcher): add PyInstaller spec + GitHub release matrix"
```

---

### Task 11: README distribution section

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: the released artifacts from Task 10.
- Produces: a teacher-facing "Easiest install" section.

- [ ] **Step 1: Add the section near the top of README.md**

```markdown
## Easiest install (no terminal)

1. Go to the [latest release](https://github.com/daxtangco/block-coding-robot/releases/latest)
   and download the file for your computer:
   - Windows: `Block-Robot.exe`
   - macOS: `Block-Robot` (right-click → Open the first time)
   - Linux: `Block-Robot` (mark executable, then run)
2. Double-click it. The launcher window opens.
3. Click **⚙️ Set up / update** once and wait — it installs everything and
   downloads the detection model.
4. Click **▶ Start IDE**. Your browser opens the IDE.

If a row shows ❌, the launcher tells you exactly what to do (for example,
install Python or join the robot's WiFi), then click **🩺 Check my system**
again.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add no-terminal launcher install section"
```

---

## Self-Review

**Spec coverage:**
- Delivery / frozen app / per-OS artifacts → Task 10.
- Two-layer Python (launcher vs IDE `.venv`) → `find_system_python` (Task 4) + `venv_python` (Task 1) + `run_setup` (Task 6); spec excludes IDE deps from the frozen bundle → `excludes=[...]` in Task 10 spec.
- Window layout B → Task 7 (buttons left, diagnostics right) + Flash button Task 9.
- Doctor as spine, ordered check table (#1–#7) → Tasks 1–3 (`run_checks(include_flash)` maps #6/#7).
- Auto-fix boundary (only Set up mutates) → Task 6 `run_setup`; all other handlers are read-only.
- `.venv` isolation (not --user/global) → Task 4 `create_venv`/`pip_install`.
- Model canonical path `models/lego_detector.pt` + download from Release → Task 5.
- Backend start from `.venv` → Task 5 `start_backend` runs `backend/main.py`.
- Reuse `builder.py` flash + `list_serial_ports` → Task 9.
- `packaging/` not `build/` → Task 10.
- doctor no-tkinter → Tasks 1–3 import only stdlib.
- Error handling: streamed output + non-zero → red/log; download retry hint + manual URL → Task 5 `download_model`; arm non-blocking → Task 2 + Task 7 `on_start` uses checks 1–5 only.
- Testing: doctor unit tests (Tasks 1–3), actions tests with temp dir + stubs (Tasks 4–6), thin view manual smoke (Tasks 7, 9), CI build smoke (Task 10).

No gaps found.

**Placeholder scan:** No TBD/TODO/"add error handling"/"similar to Task N" — every code step is complete.

**Type consistency:** `CheckResult(status,label,message,fix_hint)` used identically across Tasks 1–3, 7, 9. `venv_python(project_root)` signature consistent (Tasks 1,4,5). `_stream(cmd, log)->int` consistent (Tasks 4,5). `run_setup(project_root, log, req_files)` matches its test and caller in Task 7. `run_checks(project_root, include_flash)` return order (`Python, Virtual env, Web deps, Vision deps, Model[, arduino-cli, Arm]`) is relied on by Task 9's `results[5]` index — consistent.
