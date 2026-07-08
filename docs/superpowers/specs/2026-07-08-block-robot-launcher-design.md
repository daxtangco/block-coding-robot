# Block Robot Launcher — cross-platform GUI installer + launcher

**Date:** 2026-07-08
**Status:** Approved design, ready for implementation plan

## Problem

The IDE + detection stack (FastAPI backend, Blockly frontend, PC-side YOLOv8
detection, ESP32 arm flashing) currently requires a teacher to follow a
Windows-flavored README: install Python, install two separate dependency sets,
download a model file, discover a serial port, and join an isolated WiFi network.
Non-technical teachers make mistakes at every one of those steps, and the project
needs to run on Windows, macOS, and Linux for self-distribution to schools.

## Goal

Ship one double-clickable app per OS that gets a teacher from "downloaded a file"
to "IDE running in the browser" with no terminal, while remaining transparent
about what it is doing and touching the machine as little as possible.

## Non-goals

- No auto-installation of Python itself (guided only).
- No auto-joining of the RobotArm WiFi or auto-modifying firewall/endpoint policy.
- No multi-user server hardening — the IDE is still one host PC per classroom
  (the existing `0.0.0.0:8000` bind and single-file storage are unchanged).
- No replacement of the existing `backend/`, `frontend/`, or firmware templates.

## Delivery

A **frozen, self-contained app** built with **PyInstaller** in CI, one artifact
per OS attached to a **GitHub Release**:

- `Block-Robot-Setup.exe` (Windows)
- `Block Robot.app` (macOS)
- `Block-Robot` binary / AppImage (Linux)

The frozen app bundles its own Python + Tkinter, so it opens on a machine with
**zero** Python installed. Its job is then to detect/guide the *separate* full
Python the IDE needs, install deps into a dedicated `.venv`, download the model,
and launch everything.

Teacher happy path: download one file → double-click → click **Start IDE**.

## Two-layer Python (key subtlety)

- **Launcher Python** — the interpreter PyInstaller bundles inside the frozen
  app. Runs *only* the Tkinter window and the doctor. Never runs the IDE.
- **IDE Python** — a real system Python the teacher installs (doctor check #1).
  The `.venv` is created from *this* interpreter, and every IDE/detection process
  is spawned from `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python`
  (macOS/Linux).

This keeps the frozen app small and keeps the heavy torch/ultralytics install in
a normal, inspectable venv rather than inside the frozen bundle.

## Window layout (option B — buttons + always-on diagnostics)

```
┌──────────────────────────────────────────────┐
│              🤖 Block Robot IDE                │
├──────────────┬───────────────────────────────┤
│ ▶ Start IDE  │ ✅ Python 3.12 found          │
│ ⚙️ Set up    │ ✅ Web deps installed         │
│ 🩺 Check     │ ✅ Vision (torch) ok          │
│ 🔨 Flash     │ ✅ Model file present         │
│              │ ❌ Arm not reachable          │
│              │   → join RobotArm WiFi        │
└──────────────┴───────────────────────────────┘
```

Buttons on the left; an always-visible live diagnostics/log panel on the right.
Every action streams its output into that same panel — no hidden popups. The
diagnostics panel *is* the doctor's live output.

## The doctor is the spine

One module, `doctor.py`, is the single source of truth. It runs an ordered list
of checks; each returns `(status, human_message, fix_hint)` where `status` is one
of `ok` / `fail` and `fix_hint` is plain-English guidance.

| # | Check | Auto-fix? | Fix path |
|---|-------|-----------|----------|
| 1 | Full Python 3.8+ present on system | ❌ guide | link to python.org |
| 2 | `.venv` exists | ✅ Set up | created from IDE Python |
| 3 | Web deps installed in `.venv` | ✅ Set up | `pip install -r requirements.txt` |
| 4 | Vision deps (torch/ultralytics) in `.venv` | ✅ Set up | `pip install -r requirements-vision.txt` |
| 5 | Model file `lego_detector.pt` present | ✅ Set up | download from GitHub Release asset |
| 6 | `arduino-cli` present (Flash only) | ❌ guide | install instructions |
| 7 | Arm reachable (`ROBOTARM-6654` / 192.168.4.1) | ❌ guide | join WiFi instructions |

**Auto-fix boundary — guide-only with one auto-fix path:** the *only* thing that
mutates the machine is **Set up**, which creates `.venv`, installs both dep sets
into it, and downloads the model. Every other red row shows a plain-English hint
and a **Re-check** button; nothing else is auto-performed.

Deps install into a dedicated **`.venv`** (never `--user`, never global). This
isolates the teacher's other Python work and sidesteps the
`externally-managed-environment` error on modern macOS/Linux.

### How each button calls the doctor

- **Start IDE** → run checks 1–5; if all green, spawn `uvicorn` from `.venv` and
  open the browser; else scroll the panel to the first red row.
- **Set up / update** → run checks, perform the deps/`.venv`/model auto-fix,
  then re-run checks so the teacher sees rows flip green.
- **Check my system** → run all checks, display, fix nothing.
- **Flash the robot** → additionally requires checks 6–7, then shells out to
  `arduino-cli` (reusing existing `backend/services/builder.py` logic).

## Files

New (all cross-platform, `pathlib`-based, OS-branched where paths differ):

- `launcher.py` — Tkinter window (layout B); wires buttons → doctor; streams
  subprocess output into the diagnostics panel on a background thread so the UI
  never freezes.
- `doctor.py` — the check list above. Pure logic, no Tkinter import, so it is
  unit-testable and reused by every button. Absorbs the checks currently in
  `setup_environment.py`.
- `launcher_actions.py` — venv creation, pip install, model download (from the
  Release asset URL), uvicorn spawn, arduino-cli flash. All spawned from the
  correct `.venv` interpreter path per OS.
- `packaging/` — PyInstaller spec files plus a GitHub Actions matrix
  (windows / macos / ubuntu) that builds the three artifacts and attaches them
  to a Release. (Named `packaging/`, **not** `build/`, because `build/` is
  gitignored.)

Reused as-is:

- `backend/`, `frontend/`, `requirements.txt`, `requirements-vision.txt`.
- `backend/services/builder.py` flash logic (called by the Flash button).
- `setup_environment.py` check logic (migrated into `doctor.py`; the standalone
  script can remain as a thin wrapper or be retired).

## Error handling

- Every subprocess (pip, uvicorn, arduino-cli, model download) streams stdout +
  stderr into the diagnostics panel; a non-zero exit turns the relevant row red
  with the captured tail of the error.
- Network failures during model download show a retry hint and the direct
  Release URL as a manual fallback.
- The arm-reachable check is best-effort and never blocks Start IDE (the arm is
  only needed to actually drive the robot, and may be blocked by endpoint
  security on some managed machines — a known constraint on this project's
  primary test laptop).

## Testing

- `doctor.py` gets unit tests: each check is a pure function over a fakeable
  environment (patched `shutil.which`, patched filesystem, patched socket), so
  every `(status, message, fix_hint)` branch is covered without a real machine.
- `launcher_actions.py` venv/pip/download functions tested with a temp dir and a
  stubbed interpreter + stubbed download.
- Tkinter `launcher.py` is kept thin (view + wiring only) so it needs no
  automated UI test; manual smoke test per OS: open on a clean machine, click
  Set up, click Start IDE, confirm browser opens.
- PyInstaller artifacts smoke-tested in CI by launching headless and asserting
  the doctor runs (where a display is available) or at minimum that the binary
  starts and imports cleanly.
