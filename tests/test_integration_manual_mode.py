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
    assert settings["blynk_auth_token"] == test_settings["blynk_auth_token"]

def test_template_gpio_pins_updated():
    """Test template has correct GPIO pins."""
    template_path = Path("backend/templates/arm_controller.ino")
    content = template_path.read_text(encoding='utf-8')

    assert "const int PIN_BASE = 25" in content
    assert "const int PIN_SHOULDER = 26" in content
    assert "const int PIN_ELBOW = 27" in content
    assert "const int PIN_WRIST = 32" in content
    assert "const int PIN_GRIPPER = 33" in content

def test_template_fills_correctly(test_settings):
    """Test template engine fills placeholders."""
    template_path = Path("backend/templates/arm_controller.ino")
    template = template_path.read_text(encoding='utf-8')

    result = fill_template(template, test_settings, {}, "// test code")

    assert test_settings["wifi_ssid"] in result
    assert test_settings["wifi_password"] in result
    assert test_settings["blynk_template_id"] in result
    assert test_settings["blynk_auth_token"] in result
    assert "// test code" in result

def test_frontend_has_four_tabs():
    """Test frontend HTML has all 4 tabs."""
    html_path = Path("frontend/index.html")
    content = html_path.read_text(encoding='utf-8')

    assert 'data-workspace="setup"' in content
    assert 'data-workspace="blynk-setup"' in content
    assert 'data-workspace="poses"' in content
    assert 'data-workspace="program"' in content

def test_blynk_setup_workspace_exists():
    """Test Blynk Setup workspace div exists."""
    html_path = Path("frontend/index.html")
    content = html_path.read_text(encoding='utf-8')

    assert 'id="blynk-setup-workspace"' in content
    assert 'id="standard-setup-btn"' in content
    assert 'id="custom-setup-btn"' in content

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

def test_blynk_setup_js_exists():
    """Test Blynk Setup JavaScript exists."""
    js_path = Path("frontend/js/blynk_setup.js")
    assert js_path.exists()

    content = js_path.read_text(encoding='utf-8')
    assert "BlynkSetupGuide" in content
    assert "showStandardSetup" in content
    assert "generateWidgetSteps" in content

def test_web_serial_js_exists():
    """Test Web Serial JavaScript exists."""
    js_path = Path("frontend/js/web_serial.js")
    assert js_path.exists()

    content = js_path.read_text(encoding='utf-8')
    assert "ESP32Flasher" in content
    assert "requestPort" in content
    assert "connect" in content

def test_flash_ui_js_exists():
    """Test Flash UI JavaScript exists."""
    js_path = Path("frontend/js/flash_ui.js")
    assert js_path.exists()

    content = js_path.read_text(encoding='utf-8')
    assert "FlashUI" in content
    assert "startFlash" in content
    assert "addValidationChecklist" in content
