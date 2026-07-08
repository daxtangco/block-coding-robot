import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import launcher_actions as la


def test_find_system_python_returns_valid_interpreter():
    py = la.find_system_python()
    assert py is not None
    assert isinstance(py, str) and len(py) > 0


def test_stream_captures_output():
    lines = []
    code = la._stream([sys.executable, "-c", "print('hello-stream')"], lines.append)
    assert code == 0
    assert any("hello-stream" in ln for ln in lines)


def test_stream_reports_nonzero_exit():
    lines = []
    code = la._stream([sys.executable, "-c", "import sys; sys.exit(3)"], lines.append)
    assert code == 3


def test_stream_reports_spawn_failure_as_127():
    lines = []
    code = la._stream(["definitely-not-a-real-binary-xyz"], lines.append)
    assert code == 127
    assert any("could not run" in ln.lower() for ln in lines)


def test_find_system_python_excludes_frozen_interpreter(monkeypatch):
    # When frozen, sys.executable is the launcher .exe, not a Python, so it must
    # never be added to the candidate list. Prove it: with `which` finding
    # nothing, a frozen launcher probes nothing and returns None — if
    # sys.executable were still a candidate, it would be probed and returned.
    probed = []
    monkeypatch.setattr(la.sys, "frozen", True, raising=False)
    monkeypatch.setattr(la.shutil, "which", lambda name: None)

    def spy_run(cmd, *a, **k):
        probed.append(cmd[0])
        raise AssertionError("should not probe any interpreter")
    monkeypatch.setattr(la.subprocess, "run", spy_run)

    assert la.find_system_python() is None
    assert probed == []
