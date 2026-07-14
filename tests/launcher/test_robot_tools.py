"""Tests for the no-terminal robot-tools install (arduino-cli + esp32 core).

Network-free: we exercise the pure path/resolution logic and stub out the
subprocess-facing helpers so the retry/orchestration flow is verified without
actually downloading ~1 GB of toolchain.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import doctor
from launcher import launcher_actions as actions


# ── doctor path resolution ───────────────────────────────────────────────────

def test_arduino_cli_local_name_matches_platform():
    p = doctor.arduino_cli_local(Path("/proj"))
    assert p.parent == Path("/proj") / "tools"
    if sys.platform == "win32":
        assert p.name == "arduino-cli.exe"
    else:
        assert p.name == "arduino-cli"


def test_arduino_cli_path_prefers_system(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: "/usr/bin/arduino-cli")
    assert doctor.arduino_cli_path(Path("/proj")) == "/usr/bin/arduino-cli"


def test_arduino_cli_path_falls_back_to_local(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: None)
    local = doctor.arduino_cli_local(tmp_path)
    local.parent.mkdir(parents=True)
    local.write_text("#!/bin/sh\n")
    assert doctor.arduino_cli_path(tmp_path) == str(local)


def test_arduino_cli_path_none_when_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: None)
    assert doctor.arduino_cli_path(tmp_path) is None


def test_check_arduino_tools_fail_when_no_cli(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda _: None)
    r = doctor.check_arduino_tools(tmp_path)
    assert r.status == "fail"
    assert "arduino-cli" in r.message


def test_check_arduino_tools_fail_when_core_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "arduino_cli_path", lambda _: "/usr/bin/arduino-cli")
    monkeypatch.setattr(doctor, "esp32_core_installed", lambda *a, **k: False)
    r = doctor.check_arduino_tools(tmp_path)
    assert r.status == "fail"
    assert "esp32" in r.message


def test_check_arduino_tools_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "arduino_cli_path", lambda _: "/usr/bin/arduino-cli")
    monkeypatch.setattr(doctor, "esp32_core_installed", lambda *a, **k: True)
    r = doctor.check_arduino_tools(tmp_path)
    assert r.status == "ok"


# ── actions: asset selection ─────────────────────────────────────────────────

def test_arduino_cli_asset_known_platforms(monkeypatch):
    for plat, mach, expect in [
        ("win32", "amd64", "Windows_64bit.zip"),
        ("darwin", "arm64", "macOS_ARM64.tar.gz"),
        ("darwin", "x86_64", "macOS_64bit.tar.gz"),
        ("linux", "x86_64", "Linux_64bit.tar.gz"),
        ("linux", "aarch64", "Linux_ARM64.tar.gz"),
    ]:
        monkeypatch.setattr(actions.sys, "platform", plat)
        monkeypatch.setattr(actions.platform, "machine", lambda m=mach: m)
        asset = actions._arduino_cli_asset()
        assert asset and asset.endswith(expect), f"{plat}/{mach} → {asset}"


# ── actions: esp32 core retry loop ───────────────────────────────────────────

def test_install_esp32_core_stops_when_already_installed(monkeypatch):
    logs = []
    monkeypatch.setattr(actions, "_stream", lambda *a, **k: 0)  # update-index
    monkeypatch.setattr(actions.doctor, "esp32_core_installed", lambda *a, **k: True)
    assert actions.install_esp32_core("cli", logs.append) is True


def test_install_esp32_core_retries_then_succeeds(monkeypatch):
    logs = []
    calls = {"install": 0}

    def fake_stream(cmd, log):
        # First arg after exe is the subcommand ("core"), then the verb.
        if "install" in cmd:
            calls["install"] += 1
        return 0

    # Core reports "not installed" until the 2nd install attempt completes.
    seq = iter([False, False, False, True, True])

    def fake_installed(*a, **k):
        try:
            return next(seq)
        except StopIteration:
            return True

    monkeypatch.setattr(actions, "_stream", fake_stream)
    monkeypatch.setattr(actions.doctor, "esp32_core_installed", fake_installed)
    assert actions.install_esp32_core("cli", logs.append, retries=5) is True
    assert calls["install"] >= 2  # retried at least once


def test_install_esp32_core_gives_up_after_retries(monkeypatch):
    logs = []
    monkeypatch.setattr(actions, "_stream", lambda *a, **k: 1)
    monkeypatch.setattr(actions.doctor, "esp32_core_installed", lambda *a, **k: False)
    assert actions.install_esp32_core("cli", logs.append, retries=3) is False
    assert any("did not finish" in m for m in logs)


def test_install_robot_tools_aborts_if_cli_fails(monkeypatch):
    logs = []
    monkeypatch.setattr(actions, "install_arduino_cli", lambda *a, **k: None)
    assert actions.install_robot_tools(Path("/proj"), logs.append) is False
