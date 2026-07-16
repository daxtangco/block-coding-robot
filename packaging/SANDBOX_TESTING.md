# Testing the launcher on a clean machine (Windows Sandbox)

Goal: prove the "no terminal, out-of-the-box" experience works on a Windows PC
that has **zero dependencies** — no Python, no pip packages — the same state as a
teacher's brand-new laptop. Windows Sandbox gives a disposable clean Windows that
is discarded on close, so nothing touches your real machine.

## One-time host setup

1. Enable the Windows Sandbox feature (Win10/11 **Pro** only):
   - "Turn Windows features on or off" → tick **Windows Sandbox** → reboot, OR
   - PowerShell as admin:
     `Enable-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM" -All`
   - If the option is greyed out, enable virtualization (VT-x/AMD-V) in BIOS.
2. Create the shared test folder and put the launcher exe in it:
   - Make `C:\Users\<you>\Downloads\blockrobot-test`
   - Download `Block-Robot.exe` from the latest GitHub Release into that folder:
     https://github.com/daxtangco/block-coding-robot/releases/latest
   - Edit `HostFolder` in `packaging/BlockRobot.wsb` if your path differs.

## Run the test

1. Double-click `packaging/BlockRobot.wsb`. A clean Sandbox boots with the test
   folder on its desktop (`blockrobot`). This machine has **no Python**.

2. **Bare-machine Set up (expect the Python gate).**
   Run `Block-Robot.exe` → click **⚙️ Set up / update**.
   - EXPECT: a clear message that Python isn't found and to install it from
     python.org. PASS = plain message, no crash, no raw traceback.

3. **Install Python, then real Set up.**
   In the Sandbox, download Python 3.11+ from python.org and install it with
   **"Add python.exe to PATH"** ticked. Re-run `Block-Robot.exe` → **Set up /
   update**.
   - EXPECT: creates `.venv` under `C:\Users\WDAGUtilityAccount\BlockRobot`,
     pip-installs the web + vision dependencies (Sandbox has internet by
     default), reports **Model file present** with no download, ends with
     `✅ Setup complete.`

4. **Start IDE.**
   Click **▶ Start IDE**.
   - EXPECT: the server starts and the browser opens `http://localhost:8000`
     showing the Blockly block-coding IDE.
   - (Flashing / driving the arm needs the ESP32 hardware — out of scope here.)

5. Note pass/fail and anything surprising at each step, then **close the
   Sandbox** — all of it is discarded.

## What counts as a bug

Any step that crashes, hangs indefinitely, or shows a raw Python traceback
instead of a plain teacher-facing message. The Python-missing message in step 2
is EXPECTED, not a bug.

## Notes

- The exe on Release **v1.1.0** is the current shipping build. It does **not**
  yet include the offline-Set up and USB-driver help messages (those are on
  branch `feature/launcher-failure-ux`, not merged/released). To test those on a
  clean machine, either run from source in the Sandbox (install git + Python,
  clone, `git checkout feature/launcher-failure-ux`, `python -m
  launcher.launcher`) or cut a new release after merging.
- The two new messages don't actually need a clean room — on any machine you can
  check the offline message by turning off WiFi before Set up, and the USB
  message by clicking Flash with no ESP32 plugged in.
