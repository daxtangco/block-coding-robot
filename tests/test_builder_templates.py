from backend.services.builder import get_template_path
from pathlib import Path

def test_arm_template_is_ap_mode():
    path = get_template_path()
    assert path == Path("backend/templates/arm_controller_ap_mode.ino")
    assert path.exists()
