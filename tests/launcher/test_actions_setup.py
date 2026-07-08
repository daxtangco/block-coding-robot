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
