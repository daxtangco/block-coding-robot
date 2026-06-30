from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List

from backend.services.storage import load_poses, save_poses

router = APIRouter()

# Per-channel travel limits, matching the firmware's SERVO_MAX_ANGLE
# (base, shoulder, elbow, wrist, gripper). Base is a 360° servo; wrist is
# mechanically limited to 90°.
SERVO_MAX_ANGLE = [180, 180, 180, 90, 180]


def _validate_angles(angles, pose_name=""):
    where = f" in pose '{pose_name}'" if pose_name else ""
    if len(angles) != 5:
        raise HTTPException(400, f"Pose{where} must have exactly 5 angles (base, shoulder, elbow, wrist, gripper)")
    for i, angle in enumerate(angles):
        if not (0 <= angle <= SERVO_MAX_ANGLE[i]):
            raise HTTPException(400, f"Invalid angle{where}: {angle}. Channel {i} must be between 0 and {SERVO_MAX_ANGLE[i]}")

class PoseModel(BaseModel):
    name: str
    angles: List[int]  # [base, shoulder, elbow, wrist, gripper]

class PosesUpdate(BaseModel):
    poses: Dict[str, List[int]]

@router.get("/poses")
async def get_poses(project_name: str = "default"):
    """Get all saved poses"""
    try:
        poses = load_poses(project_name)
        return {"status": "success", "poses": poses}
    except Exception as e:
        raise HTTPException(500, f"Failed to load poses: {str(e)}")

@router.post("/poses")
async def add_pose(pose: PoseModel, project_name: str = "default"):
    """Add a new pose"""
    try:
        poses = load_poses(project_name)

        _validate_angles(pose.angles)

        # Add/update pose
        poses[pose.name] = pose.angles
        save_poses(poses, project_name)

        return {"status": "success", "message": f"Pose '{pose.name}' saved successfully", "poses": poses}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to save pose: {str(e)}")

@router.delete("/poses/{pose_name}")
async def delete_pose(pose_name: str, project_name: str = "default"):
    """Delete a pose"""
    try:
        poses = load_poses(project_name)

        if pose_name not in poses:
            raise HTTPException(404, f"Pose '{pose_name}' not found")

        # Prevent deleting HOME pose
        if pose_name == "HOME":
            raise HTTPException(400, "Cannot delete HOME pose")

        del poses[pose_name]
        save_poses(poses, project_name)

        return {"status": "success", "message": f"Pose '{pose_name}' deleted successfully", "poses": poses}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete pose: {str(e)}")

@router.put("/poses")
async def update_all_poses(update: PosesUpdate, project_name: str = "default"):
    """Replace all poses"""
    try:
        # Validate all poses
        for name, angles in update.poses.items():
            _validate_angles(angles, name)

        save_poses(update.poses, project_name)
        return {"status": "success", "message": "All poses updated successfully", "poses": update.poses}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to update poses: {str(e)}")
