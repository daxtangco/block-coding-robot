from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.services.storage import load_settings, save_settings

router = APIRouter()

class SettingsModel(BaseModel):
    wifi_ssid: str
    wifi_password: str
    blynk_template_id: str
    blynk_template_name: str
    blynk_auth_token: str

@router.get("/settings")
async def get_settings(project_name: str = "default"):
    """Get current project settings"""
    try:
        settings = load_settings(project_name)
        return {"status": "success", "settings": settings}
    except Exception as e:
        raise HTTPException(500, f"Failed to load settings: {str(e)}")

@router.post("/settings")
async def update_settings(settings: SettingsModel, project_name: str = "default"):
    """Update project settings"""
    try:
        save_settings(settings.dict(), project_name)
        return {"status": "success", "message": "Settings saved successfully"}
    except Exception as e:
        raise HTTPException(500, f"Failed to save settings: {str(e)}")
