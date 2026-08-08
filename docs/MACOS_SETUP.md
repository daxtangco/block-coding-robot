# macOS Setup — Handoff for the Mac development session

> **Read this first.** This file is written for a development session running on
> a **macOS** machine, picking up a project that was developed on Windows. Its
> job: get the Block Robot IDE + launcher running on this Mac. The code is
> already cross-platform — there are **no source changes to make**. This is a
> setup/run task, not a porting task.

## What this project is

DLSU thesis (RIAL-3-2425-C7): a low-cost 3D-printed pick-and-place robotic arm
for secondary-education. Three parts:

- **IDE** — FastAPI backend + Blockly block-coding frontend, served at
  `http://localhost:8000`. This is what runs on this Mac.
- **Arm** — an ESP32 running in WiFi Access-Point mode (`ROBOTARM-XXXX`,
  gateway `192.168.4.1`). You connect your Mac's WiFi directly to it to drive
  the arm. Optional — the IDE runs fine with no arm attached.
- **Vision** — an ESP32-CAM streams frames; a PC-side YOLOv8 model
  (`ultralytics`) does object detection. Optional — only the Vision/Train tabs
  need it.

> The camera **sees**, the Mac **thinks**, the arm **acts**.

## Current branch state

The launcher lives on the **`feature/launcher`** branch (not yet merged to
`main`). After cloning, check it out:

```bash
git checkout feature/launcher
```

## Why the code already works on macOS (don't re-port it)

An audit on the Windows side confirmed the platform-specific spots are all
guarded correctly:

- `launcher/doctor.py:29` — `venv_python()` returns `.venv/bin/python` on
  non-Windows (vs `Scripts/python.exe` on Windows). Correct for macOS.
- `backend/main.py:17` — the only Windows-only line
  (`WindowsSelectorEventLoopPolicy`) is behind `if sys.platform == 'win32'`,
  so macOS skips it.
- `launcher/launcher_actions.py` — `find_system_python()` probes
  `python3`/`python` via `shutil.which`, the normal macOS layout.
- All dependencies are pure-Python / pip wheels (see requirements below); no
  Windows-only packages.

**Do not add macOS-specific branches or "fixes" unless something actually
fails.** If a command below errors, debug that specific failure — don't
preemptively rewrite portable code.

## Prerequisites

- **Python 3.8+** — macOS system Python is often old or absent. Preferred:
  `brew install python` (gives `python3`). Verify: `python3 --version`.
- **Homebrew** — if missing: https://brew.sh
- **arduino-cli** — *only* needed for the Flash-firmware button:
  `brew install arduino-cli`. Skip if you're not flashing the ESP32 from this
  Mac.

## Setup — Option A (recommended): use the launcher GUI

The launcher is a Tkinter app that does venv creation, dependency install, and
model download for you. macOS ships Tk with the python.org / Homebrew Python.

```bash
python3 -m launcher.launcher
```

In the window:
1. Click **⚙️ Set up / update** — creates `.venv`, installs both requirement
   sets, downloads the detection model. Wait for `✅ Setup complete.`
2. Click **▶ Start IDE** — starts the backend and opens
   `http://localhost:8000` in your browser.
3. **🩺 Check my system** re-runs all checks; **🔨 Flash the robot** uploads
   firmware (needs `arduino-cli` + the ESP32 plugged in over USB).

If a check shows ❌, the panel prints exactly what to do, then click
**🩺 Check my system** again.

## Setup — Option B: manual (no GUI)

If Tkinter is unavailable or you prefer the terminal:

```bash
# from the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt      # IDE core
pip install -r requirements-vision.txt        # Vision/Train tabs (optional)

# run the server
python backend/main.py
# open http://localhost:8000
```

The server binds `0.0.0.0:8000` (so phones/tablets on the robot's WiFi can
reach it too) and prints both the localhost URL and the LAN URL on startup.

## Dependencies (for reference)

`backend/requirements.txt` (IDE core):
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
httpx==0.28.1
```

`requirements-vision.txt` (optional camera/detection):
```
ultralytics==8.4.47       # YOLOv8 detection + training
opencv-python==4.13.0.92  # reads the camera image
pyyaml==6.0.3             # reads training data.yaml
```

## macOS-specific things to watch for

- **Apple Silicon (M-series) vs Intel** — `ultralytics`/`torch` install
  arm64 wheels on Apple Silicon automatically via pip. If `pip install
  ultralytics` fails to find a wheel, upgrade pip first (`pip install -U pip`)
  and ensure Python is arm64 (`python3 -c "import platform; print(platform.machine())"`
  → `arm64`). Detection runs on CPU by default; no CUDA on Mac.
- **First launch of the frozen `.app`** (if you ever download a release build,
  not relevant when running from source) — right-click → **Open** to get past
  Gatekeeper the first time.
- **Tkinter missing** — if `python3 -m launcher.launcher` errors with
  `ModuleNotFoundError: _tkinter`, install a Tk-enabled Python:
  `brew install python-tk` (or use python.org's installer, which bundles Tk).
  This only affects Option A; Option B doesn't need Tk.
- **The frozen macOS release artifact is unproven.** The GitHub Actions macOS
  matrix leg exists but has never run (it fires only on a `v*` tag). Running
  from source (Option A/B) is the reliable path. Do not assume the `.app`
  download works until a tagged release has been built and tested.

## Connecting to the physical arm (optional)

`192.168.4.1` is the **arm's own** WiFi AP gateway, not a LAN address. To
drive the real arm: join the Mac's WiFi to `ROBOTARM-XXXX`, then the IDE's
Teach-Poses tab connects over `ws://192.168.4.1/ws`. Note: while joined to the
arm's AP you typically lose internet, so do all pip/model downloads **first**
on normal WiFi.

## Sanity check

```bash
python -m pytest tests/launcher -q     # expect 25 passed
python -c "import launcher.launcher; print('import ok')"   # no window should open
```

The full `pytest` run has 4 pre-existing failures in
`tests/test_integration_manual_mode.py` (frontend-asset assertions) that exist
on `main` too and are unrelated to the launcher — ignore them.
