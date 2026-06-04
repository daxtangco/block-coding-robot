from typing import Dict, Any

def generate_pose_definitions(poses: Dict[str, list]) -> str:
    """Convert poses dict to C++ const array declarations."""
    lines = []
    for name, angles in poses.items():
        const_name = f"POSE_{name.upper()}"
        angles_str = ", ".join(map(str, angles))
        lines.append(f"const int {const_name}[5] = {{{angles_str}}};")
    return "\n".join(lines)

def fill_template(template: str, settings: Dict[str, Any], poses: Dict[str, list], generated_code: str) -> str:
    """Replace {{placeholders}} in template with actual values."""
    replacements = {
        "{{BLYNK_TEMPLATE_ID}}": settings.get("blynk_template_id", ""),
        "{{BLYNK_TEMPLATE_NAME}}": settings.get("blynk_template_name", ""),
        "{{BLYNK_AUTH_TOKEN}}": settings.get("blynk_auth_token", ""),
        "{{WIFI_SSID}}": settings.get("wifi_ssid", ""),
        "{{WIFI_PASSWORD}}": settings.get("wifi_password", ""),
        "{{POSE_DEFINITIONS}}": generate_pose_definitions(poses),
        "{{GENERATED_CODE}}": generated_code,
    }

    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result
