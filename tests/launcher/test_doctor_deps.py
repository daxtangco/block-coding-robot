# tests/launcher/test_doctor_deps.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import doctor


def test_check_model_fail_when_absent(tmp_path):
    r = doctor.check_model(tmp_path)
    assert r.status == "fail"


def test_check_model_ok_when_present(tmp_path):
    m = tmp_path / "models" / "lego_detector.pt"
    m.parent.mkdir(parents=True)
    m.write_bytes(b"fake")
    r = doctor.check_model(tmp_path)
    assert r.status == "ok"


def test_check_tool_on_path_ok_for_python():
    # sys.executable's dir has "python"; use a tool guaranteed present.
    name = "python" if sys.platform == "win32" else "sh"
    r = doctor.check_tool_on_path(name, "Tool", "install it")
    assert r.status == "ok"


def test_check_tool_on_path_fail_for_missing():
    r = doctor.check_tool_on_path("definitely-not-a-real-tool-xyz", "Tool", "install it")
    assert r.status == "fail"
    assert r.fix_hint == "install it"


def test_check_arm_reachable_fail_on_closed_port():
    # Port 1 on localhost is virtually never open.
    r = doctor.check_arm_reachable(host="127.0.0.1", port=1, timeout=0.2)
    assert r.status == "fail"
