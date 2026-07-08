import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from launcher import launcher_actions as la


def test_download_model_writes_file(tmp_path, monkeypatch):
    def fake_urlretrieve(url, filename):
        Path(filename).write_bytes(b"MODELBYTES")
    monkeypatch.setattr(la.urllib.request, "urlretrieve", fake_urlretrieve)

    ok = la.download_model(tmp_path, log=lambda s: None, url="http://x/model.pt")
    assert ok is True
    assert (tmp_path / "models" / "lego_detector.pt").read_bytes() == b"MODELBYTES"


def test_download_model_reports_failure(tmp_path, monkeypatch):
    # Simulate a download that writes a partial .part file, then fails — this
    # exercises the cleanup branch (a boom raising before writing would leave
    # the part.unlink() branch untested).
    def boom(url, filename):
        Path(filename).write_bytes(b"PARTIAL")
        raise OSError("network down")
    monkeypatch.setattr(la.urllib.request, "urlretrieve", boom)

    logs = []
    ok = la.download_model(tmp_path, log=logs.append, url="http://x/model.pt")
    assert ok is False
    assert any("network down" in ln for ln in logs)
    # Neither the canonical model nor the partial is left behind.
    assert not (tmp_path / "models" / "lego_detector.pt").exists()
    assert not (tmp_path / "models" / "lego_detector.pt.part").exists()


def test_model_url_is_defined():
    assert isinstance(la.MODEL_URL, str)
    assert la.MODEL_URL.startswith("http")
