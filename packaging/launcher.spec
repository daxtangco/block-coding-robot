# packaging/launcher.spec
# Build: pyinstaller packaging/launcher.spec
# Produces a one-file frozen launcher that bundles Python + Tkinter.
#
# One-file mode is expressed by the spec's SHAPE: a.binaries/a.zipfiles/a.datas
# are folded into EXE() and there is no COLLECT step. (There is no `onefile`
# keyword on EXE — passing one raises TypeError at spec-parse time.)
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# The frozen launcher is a *bootstrapper*: it builds a .venv with a system
# Python and installs the heavy IDE deps (torch/ultralytics/cv2) there — hence
# they're excluded from the binary below. But the launcher still needs the app
# *source* (backend/frontend/config + requirements) and the detection model to
# exist at its project root. We bundle those here as data so a downloaded-only
# binary is self-contained; launcher.py copies them out to a writable root on
# first run. Paths are relative to this spec file (packaging/).
datas = [
    ('../backend', 'backend'),                       # server + routes/services/templates
    ('../frontend', 'frontend'),                     # the IDE web page
    ('../config.py', '.'),                           # class list + model paths
    ('../sorting_logic.py', '.'),                    # LEGOSorter — imported by backend/services/detection.py
    ('../requirements-vision.txt', '.'),             # vision deps (backend/requirements.txt rides along in backend/)
    ('../models/lego_detector.pt', 'models'),        # frozen detection model (avoids the download step)
]

a = Analysis(
    ['../launcher/launcher.py'],
    pathex=['..'],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules('launcher'),
    hookspath=[],
    runtime_hooks=[],
    excludes=['torch', 'ultralytics', 'cv2'],  # heavy IDE deps live in .venv, not here
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Block-Robot',
    console=False,
)
