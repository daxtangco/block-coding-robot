# Session handoff — launcher hardening & multi-OS release (2026-07-17)

For the Mac development session. Summary of what changed, why, current state,
and what's left. Everything below is already merged to `main` and released.

## TL;DR

Hardened the Block Robot launcher for real teacher machines and made the
"no-terminal" install work on Windows, macOS, and Linux. Three releases cut
today: **v1.1.1, v1.1.2, v1.1.3** (latest = v1.1.3). Windows was validated on a
fresh VM; macOS/Linux binaries are built but **not yet run on real machines**.

## What we shipped (in order)

### v1.1.1 — offline + USB failure UX (no-terminal)
Two teacher-facing failures now handled inside the launcher UI instead of
dumping raw errors:
- **Offline Set up:** `run_setup` checks connectivity before pip. If offline it
  shows a plain message, and if the arm is reachable it names the cause
  ("you're on the robot's WiFi (ROBOTARM-XXXX), which has no internet…").
  Code: `launcher/doctor.py::internet_reachable()`,
  gate in `launcher/launcher_actions.py::run_setup`.
- **No serial port on Flash:** shows ordered cable/driver guidance +
  `NO_SERIAL_HINT` and a **clickable driver-download link** rendered in the
  diagnostics panel (`USB_DRIVER_URL` → Silicon Labs CP210x/CH340 page).
  Code: `launcher/launcher.py` `_log_link`/`_insert_link` + `on_flash`
  no-ports branch. (`#2 arduino-cli` was already handled by the "Install robot
  tools" button — no change.)
- +5 unit tests in `tests/launcher/`.

### v1.1.2 — install on Python 3.13/3.14 (the important fix)
**Real out-of-box bug:** python.org always serves the newest Python (3.14). The
old exact pins (`fastapi==0.104.1`, `pydantic==2.5.0`, `pydantic-core==2.14.1`)
have **no prebuilt wheels for 3.13+**, so pip tried to compile pydantic-core
from Rust source and died with `linker link.exe not found` on any machine
without a C/Rust toolchain. This is exactly what a teacher hits.
- Fix: `backend/requirements.txt` switched from exact pins to **wheel-backed
  version floors** (`fastapi>=0.115`, `pydantic>=2.9`, `uvicorn[standard]>=0.30`,
  `python-multipart>=0.0.9`, `httpx>=0.27`). These resolve to cp313/cp314 wheels.
- Two API updates the newer libs require:
  - `backend/routes/settings.py`: `.dict()` → `.model_dump()` (pydantic v2)
  - `backend/main.py`: `@app.on_event("startup")` → `lifespan` context manager
    (FastAPI) — the model-warmup threads moved into `lifespan`.
- `requirements-vision.txt` unchanged — already had 3.14 wheels
  (torch/opencv/numpy/etc.).
- **Verified on real Python 3.14.4:** clean all-wheel install (no compile),
  backend imports + boots, `/health` → 200, 44 launcher tests pass.

### v1.1.3 — distinct per-OS binaries (fixes the no-terminal promise everywhere)
PyInstaller names the binary `Block-Robot` on **both** macOS and Linux (only
Windows gets `.exe`). The release job attached all artifacts by glob, so the
mac and linux files **collided and one overwrote the other** — the release only
ever showed one ambiguous `Block-Robot`.
- Fix in `.github/workflows/release-launcher.yml`: rename per-OS before upload.
- Result: the **v1.1.3 release** now has three downloadable binaries:
  - Windows: `Block-Robot.exe` (18.6 MB)
  - macOS:   `Block-Robot-macos` (17.1 MB)
  - Linux:   `Block-Robot-linux` (29.2 MB)
- README "Easiest install" updated with the new names + Linux `chmod +x` step.

## How the launcher works (context)

- Frozen binary is a **bootstrapper**: it bundles its own Python + Tkinter + the
  app source + the detection model, and on first run extracts them to
  `~/BlockRobot` (Windows/mac/Linux home dir). It then builds a `.venv` using the
  **teacher's system Python** and pip-installs the IDE deps there. Heavy deps
  (torch/ultralytics/cv2) are excluded from the binary and live only in `.venv`.
- Buttons: ▶ Start IDE · ⚙️ Set up / update · 🔧 Install robot tools ·
  🩺 Check my system · 🔨 Flash the robot.
- `launcher/doctor.py` = pure checks (no tkinter, unit-tested).
  `launcher/launcher_actions.py` = all side effects.
  `launcher/launcher.py` = thin Tkinter view.

## Verified vs. NOT verified

**Verified:**
- Windows fresh-VM cold install end-to-end (venv build + full dep download +
  bundled model + Start IDE opens the Blockly IDE). Notably pip **auto-resumed**
  a timed-out opencv download — good resilience on weak WiFi.
- Python 3.14 dep fix on the real dev machine (import + boot + /health + tests).

**NOT verified (open):**
- **macOS binary (`Block-Robot-macos`) has never been run.** ← relevant to the
  Mac session. First real test of it is pending. Likely first-run notes: right-
  click → Open to get past Gatekeeper (unsigned); it self-extracts to
  `~/BlockRobot`; needs a system Python 3.8+ (python.org) to build the venv.
- Linux binary never run (needs `python3-tk`, `chmod +x`).
- IDE feature-by-feature (Vision/Train tabs) under the newer pydantic/torch —
  only boot-tested, not click-tested.
- Robot flashing / camera — needs physical ESP32 hardware.

## Known issues we consciously deferred (not fixed)

1. **Misleading Python check when frozen.** The "Python" check row reports the
   *bundled* interpreter's version (e.g. "Python 3.11.9 found") while Set up
   looks for a *system* Python via `find_system_python()`. On a machine with no
   system Python this shows a contradictory `✅ Python found` + `❌ No Python
   found`. `check_python` should reflect the system Python when frozen.
2. **Stale PATH.** If a teacher installs Python *after* opening the launcher,
   Set up can't find it until they close & reopen the launcher (a running
   process keeps its old PATH). No hint tells them to restart.
   → Both are Windows-audience issues the user chose to leave for now.

## Suggested next steps

- **Mac session:** actually run `Block-Robot-macos` on a Mac and record what
  happens (Gatekeeper, venv build, Start IDE). That's the biggest untested gap.
- Optionally fix the two deferred Python-detection issues above.
- Consider feature-testing Vision/Train under the upgraded deps.

## Repo state

- Branch: `main`, latest release tag `v1.1.3`.
- Feature work merged from `feature/launcher-failure-ux` (now merged; safe to
  delete).
- Testing helpers live in `packaging/`: `BlockRobot.wsb` (Windows Sandbox
  config), `SANDBOX_TESTING.md`, `VM_TEST_RESULTS.md`.
- Note: `validate.py` has an uncommitted pre-existing change unrelated to this
  work — left untouched.
