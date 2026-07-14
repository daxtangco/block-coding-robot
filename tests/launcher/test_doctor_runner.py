import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import doctor


def test_run_checks_core_order(tmp_path):
    results = doctor.run_checks(tmp_path, include_flash=False)
    labels = [r.label for r in results]
    assert labels == ["Python", "Virtual env", "Web deps", "Vision deps", "Model"]


def test_run_checks_includes_flash(tmp_path):
    results = doctor.run_checks(tmp_path, include_flash=True)
    labels = [r.label for r in results]
    assert labels[-2:] == ["Robot tools", "Arm"]


def test_all_ok_and_first_failure():
    good = [doctor.CheckResult("ok", "A", "x")]
    bad = [doctor.CheckResult("ok", "A", "x"),
           doctor.CheckResult("fail", "B", "y")]
    assert doctor.all_ok(good) is True
    assert doctor.all_ok(bad) is False
    assert doctor.first_failure(good) is None
    assert doctor.first_failure(bad).label == "B"
