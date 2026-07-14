"""Side-effecting operations for the launcher.

Every operation streams subprocess output through a `log` callable so the
Tkinter diagnostics panel can show progress live. Nothing here imports tkinter.
"""
import os
import platform
import shutil
import subprocess
import sys
import time
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
    try:
        part.replace(dest)
    except OSError as e:
        log(f"ERROR: could not finalize model file: {e}")
        if part.exists():
            part.unlink()
        return False
    log("Model downloaded.")
    return True


def start_backend(project_root: Path, log) -> subprocess.Popen:
    root = Path(project_root)
    py = venv_python(root)
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "backend.log"
    log("Starting IDE server on http://localhost:8000 …")
    # The child inherits its own handle, so close the parent copy right
    # after spawn to avoid leaking (or, on Windows, locking) the file.
    with open(log_path, "w") as logf:
        proc = subprocess.Popen(
            [str(py), str(root / "backend" / "main.py")],
            cwd=str(root),
            stdout=logf, stderr=subprocess.STDOUT,
        )
    # Give the server a moment; if it dies immediately, surface why.
    time.sleep(2)
    if proc.poll() is not None:
        log(f"ERROR: IDE server exited immediately (code {proc.returncode}). "
            f"See {log_path} for details, then click Set up again.")
    return proc


# ── Robot-flashing toolchain (arduino-cli + esp32 core + libs) ───────────────
#
# The esp32 core is a ~1 GB download (dual Xtensa/RISC-V compiler toolchains)
# and Espressif's servers throttle hard from some regions. So the core install
# runs in a resume-retry loop: arduino-cli caches partial downloads, so each
# retry picks up where the last left off rather than starting over.

# The board-manager URL lives in doctor so the install and the readiness check
# use one source of truth; re-exported here for the install calls below.
ESP32_BOARD_URL = doctor.ESP32_BOARD_URL

# Arduino libraries the firmware templates #include. Names are the exact
# registry names; arduino-cli pulls dependencies (e.g. Adafruit BusIO,
# ESPAsyncTCP) automatically. This exact set is verified to compile the
# AP-mode template against esp32 core 3.3.10.
#   - ESP Async WebServer / Async TCP: the ESP32Async fork, the one maintained
#     for esp32 core 3.x (older ESPAsyncWebServer forks fail to compile on it).
FIRMWARE_LIBS = [
    "Adafruit PWM Servo Driver Library",  # PCA9685 servo driver
    "ArduinoJson",                        # WebSocket message (de)serialization
    "Async TCP",                          # dependency of the async web server
    "ESP Async WebServer",                # AP-mode embedded web UI + WebSocket
]
# Back-compat alias (kept for any external callers/tests).
ADAFRUIT_PWM_LIB = FIRMWARE_LIBS[0]

# arduino-cli release archives, keyed by (platform, machine-is-arm).
_ARDUINO_CLI_BASE = "https://downloads.arduino.cc/arduino-cli/"


def _arduino_cli_asset() -> Optional[str]:
    """Filename of the arduino-cli archive for this OS/arch, or None."""
    machine = platform.machine().lower()
    is_arm = machine in ("arm64", "aarch64")
    if sys.platform == "win32":
        return "arduino-cli_latest_Windows_64bit.zip"
    if sys.platform == "darwin":
        return ("arduino-cli_latest_macOS_ARM64.tar.gz" if is_arm
                else "arduino-cli_latest_macOS_64bit.tar.gz")
    if sys.platform.startswith("linux"):
        return ("arduino-cli_latest_Linux_ARM64.tar.gz" if is_arm
                else "arduino-cli_latest_Linux_64bit.tar.gz")
    return None


def install_arduino_cli(project_root: Path, log) -> Optional[str]:
    """Download a private arduino-cli into <root>/tools. Returns its path or None.

    Skips the download if arduino-cli is already resolvable (system PATH or a
    prior local install).
    """
    existing = doctor.arduino_cli_path(project_root)
    if existing:
        log(f"arduino-cli already available: {existing}")
        return existing

    asset = _arduino_cli_asset()
    if not asset:
        log(f"ERROR: no arduino-cli build for this platform ({sys.platform}/"
            f"{platform.machine()}). Install it manually from arduino.cc.")
        return None

    tools = doctor.tools_dir(project_root)
    tools.mkdir(parents=True, exist_ok=True)
    url = _ARDUINO_CLI_BASE + asset
    archive = tools / asset
    log(f"Downloading arduino-cli from {url} …")
    try:
        urllib.request.urlretrieve(url, str(archive))
    except Exception as e:
        log(f"ERROR: arduino-cli download failed: {e}")
        if archive.exists():
            archive.unlink()  # don't leave a partial archive behind
        return None

    log("Extracting arduino-cli …")
    try:
        _extract_archive(archive, tools)
    except Exception as e:
        log(f"ERROR: could not extract arduino-cli: {e}")
        return None
    finally:
        if archive.exists():
            archive.unlink()

    cli = doctor.arduino_cli_local(project_root)
    if not cli.exists():
        # Official archives place the binary at the root, but guard against a
        # future layout change by searching one level down before giving up.
        found = next((p for p in tools.rglob(cli.name) if p.is_file()), None)
        if found and found != cli:
            found.replace(cli)
        if not cli.exists():
            log("ERROR: arduino-cli not found after extraction.")
            return None
    if sys.platform != "win32":
        cli.chmod(0o755)
    log(f"arduino-cli installed: {cli}")
    return str(cli)


def _extract_archive(archive: Path, dest: Path) -> None:
    """Extract a .zip or .tar.gz into dest, refusing members that escape it."""
    dest = dest.resolve()

    def _safe(name: str) -> Path:
        target = (dest / name).resolve()
        if dest not in target.parents and target != dest:
            raise ValueError(f"unsafe path in archive: {name}")
        return target

    if str(archive).endswith(".zip"):
        import zipfile
        with zipfile.ZipFile(archive) as z:
            for n in z.namelist():
                _safe(n)
            z.extractall(dest)
    else:
        import tarfile
        with tarfile.open(archive) as t:
            for m in t.getmembers():
                _safe(m.name)
            # data filter (py3.12+) blocks unsafe members defensively too.
            try:
                t.extractall(dest, filter="data")
            except TypeError:
                t.extractall(dest)


def install_esp32_core(cli: str, log, retries: int = 5) -> bool:
    """Install the esp32:esp32 core, retrying so throttled downloads resume.

    arduino-cli keeps partial downloads in its staging cache, so a failed
    attempt is not wasted — the next retry continues from there.
    """
    log("Updating board index (registering esp32 board URL) …")
    if _stream([cli, "core", "update-index",
                "--additional-urls", ESP32_BOARD_URL], log) != 0:
        log("WARNING: index update failed; attempting install anyway.")

    if doctor.esp32_core_installed(cli, ESP32_BOARD_URL):
        log("esp32 core already installed.")
        return True

    log("Installing esp32 core (~1 GB — this can take a while on a slow link; "
        "it resumes if interrupted) …")
    for attempt in range(1, retries + 1):
        log(f"── esp32 core install attempt {attempt}/{retries} ──")
        code = _stream([cli, "core", "install", "esp32:esp32",
                        "--additional-urls", ESP32_BOARD_URL], log)
        if code == 0 and doctor.esp32_core_installed(cli, ESP32_BOARD_URL):
            log("esp32 core installed.")
            return True
        if attempt < retries:
            log(f"Attempt {attempt} did not complete; retrying (resumes from "
                f"cached partial download) …")
    log("ERROR: esp32 core install did not finish after "
        f"{retries} attempts. Check your connection (a VPN often helps from "
        "throttled regions), then click Install robot tools again — progress "
        "so far is cached and will resume.")
    return False


def install_arduino_lib(cli: str, lib: str, log) -> bool:
    if _stream([cli, "lib", "install", lib], log) != 0:
        log(f"ERROR: could not install library '{lib}'.")
        return False
    return True


def install_robot_tools(project_root: Path, log) -> bool:
    """Full no-terminal firmware toolchain: arduino-cli + esp32 core + libs."""
    cli = install_arduino_cli(project_root, log)
    if not cli:
        return False
    if not install_esp32_core(cli, log):
        return False
    log("Installing firmware libraries …")
    for lib in FIRMWARE_LIBS:
        if not install_arduino_lib(cli, lib, log):
            return False
    log("✅ Robot tools ready — you can now Flash the robot.")
    return True


def flash_firmware(project_root: Path, port: str, sketch_path: Path, log) -> bool:
    cli = doctor.arduino_cli_path(project_root)
    if not cli:
        log("ERROR: arduino-cli not installed. Click 'Install robot tools' first.")
        return False
    sketch_dir = Path(sketch_path).parent
    cmd = [
        cli, "compile", "--upload",
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
