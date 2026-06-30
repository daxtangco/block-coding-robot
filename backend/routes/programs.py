from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any

from backend.services.storage import load_programs, save_programs

router = APIRouter()


class ProgramModel(BaseModel):
    name: str
    workspace: Any  # Blockly workspace serialization (JSON object)


@router.get("/programs")
async def get_programs(project_name: str = "default"):
    """Get all saved block programs (names + their saved workspaces)."""
    try:
        programs = load_programs(project_name)
        return {"status": "success", "programs": programs}
    except Exception as e:
        raise HTTPException(500, f"Failed to load programs: {str(e)}")


@router.post("/programs")
async def save_program(program: ProgramModel, project_name: str = "default"):
    """Save (or overwrite) a named block program."""
    try:
        programs = load_programs(project_name)
        programs[program.name] = program.workspace
        save_programs(programs, project_name)
        return {"status": "success", "message": f"Program '{program.name}' saved successfully", "programs": programs}
    except Exception as e:
        raise HTTPException(500, f"Failed to save program: {str(e)}")


@router.delete("/programs/{program_name}")
async def delete_program(program_name: str, project_name: str = "default"):
    """Delete a saved block program."""
    try:
        programs = load_programs(project_name)
        if program_name not in programs:
            raise HTTPException(404, f"Program '{program_name}' not found")
        del programs[program_name]
        save_programs(programs, project_name)
        return {"status": "success", "message": f"Program '{program_name}' deleted successfully", "programs": programs}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete program: {str(e)}")
