import json
from pathlib import Path
from typing import Dict, Any

PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

def get_project_dir(project_name: str = "default") -> Path:
    """Get or create project directory"""
    project_dir = PROJECTS_DIR / project_name
    project_dir.mkdir(exist_ok=True)
    return project_dir

def load_settings(project_name: str = "default") -> Dict[str, Any]:
    """Load project settings from JSON file"""
    settings_path = get_project_dir(project_name) / "settings.json"
    if settings_path.exists():
        return json.loads(settings_path.read_text())
    # Return default settings
    return {
        "wifi_ssid": "",
        "wifi_password": "",
        "blynk_template_id": "",
        "blynk_template_name": "",
        "blynk_auth_token": "",
    }

def save_settings(settings: Dict[str, Any], project_name: str = "default"):
    """Save project settings to JSON file"""
    settings_path = get_project_dir(project_name) / "settings.json"
    settings_path.write_text(json.dumps(settings, indent=2))

def load_poses(project_name: str = "default") -> Dict[str, list]:
    """Load saved poses from JSON file"""
    poses_path = get_project_dir(project_name) / "poses.json"
    if poses_path.exists():
        return json.loads(poses_path.read_text())
    # Return default poses
    return {
        "HOME": [90, 90, 90, 90, 30],
    }

def save_poses(poses: Dict[str, list], project_name: str = "default"):
    """Save poses to JSON file"""
    poses_path = get_project_dir(project_name) / "poses.json"
    poses_path.write_text(json.dumps(poses, indent=2))
