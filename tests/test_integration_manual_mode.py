"""Integration tests for manual mode hardware integration."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.template_engine import fill_template
import json
from pathlib import Path

client = TestClient(app)

@pytest.fixture
def test_settings():
    """Test settings fixture."""
    return {
        "wifi_ssid": "TestWiFi",
        "wifi_password": "testpass123",
        "blynk_template_id": "TMPL123456",
        "blynk_template_name": "Test Robot",
        "blynk_auth_token": "test_token_abc"
    }

def test_settings_save_and_load(test_settings, tmp_path):
    """Test settings can be saved and loaded."""
    # Save settings
    response = client.post("/api/settings", json=test_settings)
    assert response.status_code == 200

    # Load settings
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    # API returns nested structure: {"status": "success", "settings": {...}}
    settings = data.get("settings", data)
    assert settings["wifi_ssid"] == test_settings["wifi_ssid"]

def test_template_has_servo_channels():
    """The AP-mode template maps the five joints to PCA9685 channels."""
    content = Path("backend/templates/arm_controller_ap_mode.ino").read_text(encoding='utf-8')

    for name in ("SERVO_BASE", "SERVO_SHOULDER", "SERVO_ELBOW", "SERVO_WRIST", "SERVO_GRIPPER"):
        assert name in content

def test_template_fills_correctly(test_settings):
    """Test template engine fills placeholders and leaves none behind."""
    template = Path("backend/templates/arm_controller_ap_mode.ino").read_text(encoding='utf-8')

    result = fill_template(template, test_settings, {"HOME": [90, 120, 120, 75, 5]}, "// test code")

    assert "// test code" in result
    assert "const int POSE_HOME[5] = {90, 120, 120, 75, 5};" in result
    assert "{{" not in result

def test_flash_options_in_build_modal():
    """Test build modal has flash options."""
    html_path = Path("frontend/index.html")
    content = html_path.read_text(encoding='utf-8')

    assert 'id="flash-usb-btn"' in content
    assert 'id="download-bin-btn"' in content
    assert 'Flash via USB' in content

def test_documentation_exists():
    """Test required documentation files exist."""
    assert Path("docs/BLYNK_SETUP_GUIDE.md").exists()
    assert Path("docs/HARDWARE_PINOUT.md").exists()
    assert Path("QUICKSTART.md").exists()  # QUICKSTART is in root directory

