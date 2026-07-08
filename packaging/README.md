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
