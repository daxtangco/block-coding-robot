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
        # Joint move order (servo channels): wrist, elbow, shoulder, base, gripper.
        "joint_order": [3, 2, 1, 0, 4],
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
    # Return default poses. HOME matches the firmware default:
    # base 180, shoulder 90, elbow 90, wrist 90, gripper 0.
    return {
        "HOME": [180, 90, 90, 90, 0],
    }

def save_poses(poses: Dict[str, list], project_name: str = "default"):
    """Save poses to JSON file"""
    poses_path = get_project_dir(project_name) / "poses.json"
    poses_path.write_text(json.dumps(poses, indent=2))

def load_drop_zones(project_name: str = "default") -> Dict[str, Any]:
    """Load the drop-zone masks (exclusion ROI) for the Vision tab.

    Shape: {"enabled": bool, "zones": [{"left","top","right","bottom"}, ...]}
    where each value is a fraction (0..1) of the frame. Default = enabled with no
    zones, i.e. the whole frame is valid pickup space until the user draws bins.
    """
    path = get_project_dir(project_name) / "drop_zones.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"enabled": True, "zones": []}

def save_drop_zones(drop_zones: Dict[str, Any], project_name: str = "default"):
    """Save the drop-zone masks to JSON file."""
    path = get_project_dir(project_name) / "drop_zones.json"
    path.write_text(json.dumps(drop_zones, indent=2))

def load_programs(project_name: str = "default") -> Dict[str, Any]:
    """Load saved block programs. Each value is a Blockly workspace
    serialization (the blocks themselves, not the generated C++)."""
    programs_path = get_project_dir(project_name) / "programs.json"
    if programs_path.exists():
        return json.loads(programs_path.read_text())
    return {}

def save_programs(programs: Dict[str, Any], project_name: str = "default"):
    """Save block programs to JSON file"""
    programs_path = get_project_dir(project_name) / "programs.json"
    programs_path.write_text(json.dumps(programs, indent=2))
