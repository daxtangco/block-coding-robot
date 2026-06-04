from backend.services.builder import get_template_path
from pathlib import Path

def test_ap_mode_template():
    path = get_template_path(use_ap_mode=True)
    assert path == Path("backend/templates/arm_controller_ap_mode.ino")
    assert path.exists()

def test_pca9685_template():
    path = get_template_path(use_pca9685=True, use_ap_mode=False)
    assert path == Path("backend/templates/arm_controller_pca9685.ino")

def test_gpio_template():
    path = get_template_path(use_pca9685=False, use_ap_mode=False)
    assert path == Path("backend/templates/arm_controller.ino")

def test_default_template():
    # Default should be PCA9685 with no AP mode (legacy behavior)
    path = get_template_path()
    assert path == Path("backend/templates/arm_controller_pca9685.ino")

def test_ap_mode_overrides_pca9685():
    # AP mode takes priority over use_pca9685 parameter
    path = get_template_path(use_pca9685=False, use_ap_mode=True)
    assert path == Path("backend/templates/arm_controller_ap_mode.ino")
