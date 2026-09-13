"""
FastAPI Router for Supabase Database Telemetry and Direct Operations.
Allows status inspection and verifies connectivity from the backend service.
"""
from fastapi import APIRouter, HTTPException, Query, Body  # type: ignore # pyrefly: ignore [missing-import]
from typing import Optional, Dict, Any, List
from app.services.supabase_service import get_supabase_service  # type: ignore # pyrefly: ignore [missing-import]

router = APIRouter(prefix="", tags=["Supabase Database Integration"])


@router.get("/status")
def get_supabase_status():
    """Check Supabase connection status, credentials configuration, and remote ping."""
    service = get_supabase_service()
    return service.check_connection()


@router.post("/test-camera")
def create_test_camera(payload: Dict[str, Any] = Body(...)):
    """Insert a camera into Supabase PostgreSQL."""
    service = get_supabase_service()
    if not payload.get("id") or not payload.get("name"):
        raise HTTPException(status_code=400, detail="id and name are required for camera insertion.")
    return service.insert_camera(payload)


@router.get("/camera/{camera_id}")
def get_camera_record(camera_id: str):
    """Fetch camera record by ID from Supabase."""
    service = get_supabase_service()
    cam = service.get_camera(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail=f"Camera {camera_id} not found.")
    return cam


@router.get("/cameras")
def list_cameras_endpoint(limit: int = Query(50, ge=1, le=500), dept_id: Optional[str] = Query(None)):
    """List cameras with optional department filter."""
    service = get_supabase_service()
    return service.list_cameras(limit=limit, dept_id=dept_id)


@router.post("/test-detection")
def insert_test_detection(payload: Dict[str, Any] = Body(...)):
    """Insert a test License Plate / AI Detection record into Supabase."""
    service = get_supabase_service()
    return service.insert_license_plate_detection(payload)


@router.get("/detections")
def list_detections_endpoint(
    camera_id: Optional[str] = Query(None),
    plate_number: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500)
):
    """List recent license plate detections from Supabase."""
    service = get_supabase_service()
    return service.get_license_plate_detections(camera_id=camera_id, plate_number=plate_number, limit=limit)
