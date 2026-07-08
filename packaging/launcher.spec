# packaging/launcher.spec
# Build: pyinstaller packaging/launcher.spec
# Produces a one-file frozen launcher that bundles Python + Tkinter.
#
# One-file mode is expressed by the spec's SHAPE: a.binaries/a.zipfiles/a.datas
# are folded into EXE() and there is no COLLECT step. (There is no `onefile`
# keyword on EXE — passing one raises TypeError at spec-parse time.)
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
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Block-Robot',
    console=False,
)
