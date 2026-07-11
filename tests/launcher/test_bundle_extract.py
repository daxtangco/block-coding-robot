"""Tests for the frozen-binary first-run bootstrap (ensure_app_source).

The frozen launcher bundles the app source + model and copies them out to a
writable project root on first run. These tests simulate frozen mode with a
fake _MEIPASS and verify the extraction is complete and non-destructive.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import launcher as L


def _make_bundle(tmp_path):
    """Create a fake PyInstaller bundle dir mirroring what the spec ships."""
    b = tmp_path / "meipass"
    (b / "backend").mkdir(parents=True)
    (b / "backend" / "main.py").write_text("server")
    (b / "frontend").mkdir()
    (b / "frontend" / "index.html").write_text("page")
    (b / "models").mkdir()
    (b / "models" / "lego_detector.pt").write_bytes(b"MODELBYTES")
    (b / "config.py").write_text("cfg")
    (b / "sorting_logic.py").write_text("sorter")
    (b / "requirements-vision.txt").write_text("ultralytics")
    return b


def test_ensure_app_source_noop_when_not_frozen(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", False, raising=False)
    root = tmp_path / "root"
    L.ensure_app_source(root, lambda *_: None)
    # Not frozen: must not create/populate anything.
    assert not root.exists() or not any(root.iterdir())


def test_ensure_app_source_extracts_all_bundled_items(tmp_path, monkeypatch):
    bundle = _make_bundle(tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(L, "bundle_dir", lambda: bundle)
    root = tmp_path / "BlockRobot"

    L.ensure_app_source(root, lambda *_: None)

    assert (root / "backend" / "main.py").read_text() == "server"
    assert (root / "frontend" / "index.html").read_text() == "page"
    assert (root / "models" / "lego_detector.pt").read_bytes() == b"MODELBYTES"
    assert (root / "config.py").read_text() == "cfg"
    assert (root / "sorting_logic.py").read_text() == "sorter"
    assert (root / "requirements-vision.txt").read_text() == "ultralytics"


def test_ensure_app_source_is_idempotent_and_nondestructive(tmp_path, monkeypatch):
    bundle = _make_bundle(tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(L, "bundle_dir", lambda: bundle)
    root = tmp_path / "BlockRobot"

    L.ensure_app_source(root, lambda *_: None)
    # Simulate a user edit / existing state, then re-run.
    (root / "backend" / "main.py").write_text("USER-EDIT")
    L.ensure_app_source(root, lambda *_: None)

    # Existing files are preserved, not clobbered by the bundled copy.
    assert (root / "backend" / "main.py").read_text() == "USER-EDIT"
