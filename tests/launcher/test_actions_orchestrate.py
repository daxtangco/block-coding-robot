# tests/launcher/test_actions_orchestrate.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import launcher_actions as la


def test_run_setup_happy_path(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(la, "find_system_python", lambda: "python3")
    monkeypatch.setattr(la, "create_venv", lambda root, py, log: calls.append("venv") or True)
    monkeypatch.setattr(la, "pip_install", lambda root, reqs, log: calls.append(("pip", tuple(reqs))) or True)
    monkeypatch.setattr(la, "download_model", lambda root, log, **k: calls.append("model") or True)

    ok = la.run_setup(tmp_path, log=lambda s: None)
    assert ok is True
    assert "venv" in calls and "model" in calls


def test_run_setup_aborts_when_no_python(tmp_path, monkeypatch):
    monkeypatch.setattr(la, "find_system_python", lambda: None)
    logs = []
    ok = la.run_setup(tmp_path, log=logs.append)
    assert ok is False
    assert any("Python" in ln for ln in logs)


def test_run_setup_skips_model_download_when_present(tmp_path, monkeypatch):
    m = tmp_path / "models" / "lego_detector.pt"
    m.parent.mkdir(parents=True)
    m.write_bytes(b"x")
    monkeypatch.setattr(la, "find_system_python", lambda: "python3")
    monkeypatch.setattr(la, "create_venv", lambda *a, **k: True)
    monkeypatch.setattr(la, "pip_install", lambda *a, **k: True)
    called = {"model": False}
    monkeypatch.setattr(la, "download_model", lambda *a, **k: called.__setitem__("model", True) or True)

    ok = la.run_setup(tmp_path, log=lambda s: None)
    assert ok is True
    assert called["model"] is False
