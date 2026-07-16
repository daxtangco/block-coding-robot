# Launcher out-of-box test — fresh VM (2026-07-16)

Test of the frozen `Block-Robot.exe` (Release **v1.1.0**) on a clean Windows 11
VMware VM. Goal: verify the whole no-terminal Set up → Start IDE flow on a
machine with **zero project dependencies**.

**Result: PASS end-to-end.** Cold first-run built everything from scratch and the
IDE server started.

## Environment

- Windows 11 (VMware Workstation guest), user `daxta`.
- System Python: Microsoft Store `python3.EXE` (used to build the venv).
- Project root (frozen self-extract target): `C:\Users\daxta\BlockRobot`.
- Started truly clean: initial checks showed **No .venv / Web deps / Vision deps
  / Model** all ❌ — confirming nothing was pre-installed.

## What happened, in order

1. **First-run bootstrap (frozen self-extract).** The launcher copied its bundled
   app source out to the writable project root:
   `backend`, `frontend`, `config.py`, `sorting_logic.py`,
   `requirements-vision.txt`, `models`. ✅
2. **venv created from scratch** using the Microsoft Store Python. ✅
3. **pip self-upgraded** 25.0.1 → 26.1.2. ✅
4. **Web deps installed cold** (fastapi/uvicorn/pydantic/httpx + deps, all
   downloaded fresh). ✅
5. **Vision deps installed cold** — the heavy set: torch (122 MB), opencv
   (40 MB), scipy (36 MB), polars-runtime (52 MB), matplotlib, numpy, etc. ✅
6. **Model: "already present — skipping download."** The bundled
   `lego_detector.pt` was found; no network fetch needed. ✅
7. **`✅ Setup complete.`**
8. Subsequent Set up clicks were **idempotent** — `.venv already exists` and every
   package `already satisfied`, no reinstalls. ✅
9. **`Starting IDE server on http://localhost:8000`** — server launched, final
   re-check all 5 rows green. ✅ (Browser opened the IDE — confirmed separately.)

## Notable findings

1. **Network resilience proven (good).** During the opencv download the
   connection timed out mid-file:
   `WARNING: Connection timed out while downloading. Attempting to resume
   incomplete download (18.1 MB/40.2 MB, attempt 1)`. pip **auto-resumed and
   completed** the download. So a flaky connection during the big vision install
   self-recovers rather than failing Set up — important for teachers on weak WiFi.

2. **Displayed Python version vs. venv Python (minor, cosmetic).** The check row
   reads **"Python 3.11.9 found"**, but the installed wheels are all **cp312**
   (e.g. `torch-2.13.0-cp312`, `pydantic_core-...-cp312`), meaning the venv was
   actually built with **Python 3.12** (the Microsoft Store python). The "3.11.9"
   is the *frozen launcher's own* bundled interpreter (from the PyInstaller CI
   build), not the interpreter running the IDE. Both are ≥3.8 so nothing breaks,
   but the reported version is misleading — worth clarifying the label in a
   follow-up (e.g. report the venv's Python, or label it "Launcher Python").

3. **The busy-lock and Start gate behaved correctly.** Clicking Start IDE before
   Set up finished produced `⏳ Busy — please wait…` and
   `❌ Can't start yet: Vision deps` — both are the guards working as designed,
   not errors.

## Coverage / caveats

- This exe is **v1.1.0** and does **not** contain the unreleased offline-Set up
  and USB-driver-help messages (branch `feature/launcher-failure-ux`). Those
  still need a from-source run or a new release to test.
- Robot flashing and the camera were not tested (no ESP32 hardware in the VM).
- The IDE UI itself (Blockly tabs, Program/Vision panels) was loaded but not
  exercised feature-by-feature.
