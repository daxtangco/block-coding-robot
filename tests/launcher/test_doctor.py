import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import doctor


def test_check_python_ok_on_current_interpreter():
    r = doctor.check_python(min_major=3, min_minor=8)
    assert r.status == "ok"
    assert "Python" in r.message


def test_check_python_fail_when_floor_too_high():
    r = doctor.check_python(min_major=99, min_minor=0)
    assert r.status == "fail"
    assert "python.org" in r.fix_hint


def test_venv_python_path_is_os_correct(tmp_path):
    p = doctor.venv_python(tmp_path)
    if sys.platform == "win32":
        assert p == tmp_path / ".venv" / "Scripts" / "python.exe"
    else:
        assert p == tmp_path / ".venv" / "bin" / "python"


def test_check_venv_fail_when_missing(tmp_path):
    r = doctor.check_venv(tmp_path)
    assert r.status == "fail"


def test_check_venv_ok_when_interpreter_present(tmp_path):
    py = doctor.venv_python(tmp_path)
    py.parent.mkdir(parents=True)
    py.write_text("")
    r = doctor.check_venv(tmp_path)
    assert r.status == "ok"


def test_internet_reachable_false_on_closed_port():
    # Port 1 on localhost is virtually never open — stands in for "offline".
    assert doctor.internet_reachable(host="127.0.0.1", port=1, timeout=0.2) is False


def test_usb_driver_constants_present():
    assert doctor.USB_DRIVER_URL.startswith("http")
    assert isinstance(doctor.NO_SERIAL_HINT, str) and doctor.NO_SERIAL_HINT
