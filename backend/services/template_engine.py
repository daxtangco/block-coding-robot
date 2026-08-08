import re
from typing import Dict, Any

# Pose consts are declared as POSE_<NAME.upper()>. The frontend generator
# references them by raw pose name, so a pose whose name has lowercase letters
# (e.g. "PICKUP2x2") would emit POSE_PICKUP2x2 and fail to match the declared
# POSE_PICKUP2X2. Normalizing here makes the reference case-insensitive to
# whatever the (possibly cached) frontend sent.
_POSE_REF = re.compile(r"\bPOSE_(\w+)")

def generate_pose_definitions(poses: Dict[str, list]) -> str:
    """Convert poses dict to C++ const array declarations."""
    lines = []
    for name, angles in poses.items():
        const_name = f"POSE_{name.upper()}"
        angles_str = ", ".join(map(str, angles))
        lines.append(f"const int {const_name}[5] = {{{angles_str}}};")
    return "\n".join(lines)

def normalize_pose_refs(code: str) -> str:
    """Uppercase POSE_<name> identifiers so they match generated declarations."""
    return _POSE_REF.sub(lambda m: f"POSE_{m.group(1).upper()}", code)

def fill_template(template: str, settings: Dict[str, Any], poses: Dict[str, list], generated_code: str) -> str:
    """Replace {{placeholders}} in template with actual values."""
    replacements = {
        "{{WIFI_SSID}}": settings.get("wifi_ssid", ""),
        "{{WIFI_PASSWORD}}": settings.get("wifi_password", ""),
        "{{POSE_DEFINITIONS}}": generate_pose_definitions(poses),
        "{{GENERATED_CODE}}": normalize_pose_refs(generated_code),
    }

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result
