"""
FastAPI Router for Intel OpenVINO License Plate Recognition (LPR) Service.
Modular integration with CCTV Registry, Watchlists, and Video Analytics.
"""
import os
import shutil
import tempfile
from datetime import datetime, timezone
from fastapi import APIRouter, File, UploadFile, Form, HTTPException  # type: ignore # pyrefly: ignore [missing-import]

from app.services.lpr import (  # type: ignore # pyrefly: ignore [missing-import]
    get_lpr_pipeline,
    LprImageResponse,
    LprVideoResponse,
    LprStatusResponse
)
from app.services.lpr.model_downloader import ensure_models_available, SAMPLES_DIR  # type: ignore # pyrefly: ignore [missing-import]

router = APIRouter(prefix="", tags=["AI License Plate Recognition"])

@router.get("/status", response_model=LprStatusResponse)
def get_lpr_engine_status():
    """Retrieve operational status, active hardware device (CPU/GPU/NPU), and model health."""
    pipeline = get_lpr_pipeline()
    return pipeline.get_status()

@router.post("/process-image", response_model=LprImageResponse)
async def process_image_for_lpr(
    file: UploadFile = File(...),
    camera_id: str = Form("CAM-ANPR-01"),
    annotate: bool = Form(True)
):
    """
    Process an uploaded image file (JPEG/PNG) to detect and recognize vehicle license plates.
    Correlates results against the law enforcement vehicle watchlist.
    """
    pipeline = get_lpr_pipeline()
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty image file provided.")

    response = pipeline.process_image_bytes(
        contents,
        camera_id=camera_id,
        return_annotated=annotate
    )

    # Correlate and append to platform ANPR records & audit log
    if response.success and response.detections:
        try:
            from backend.main import ANPR_DETECTIONS, AUDIT_LOGS  # type: ignore # pyrefly: ignore [missing-import]
            from backend.models import AnprDetection, AuditLog  # type: ignore # pyrefly: ignore [missing-import]

            for det in response.detections:
                new_det_id = f"DET-{len(ANPR_DETECTIONS)+1:04d}"
                ANPR_DETECTIONS.append(AnprDetection(
                    id=new_det_id,
                    camera_id=det.camera_id,
                    camera_name=f"Camera {det.camera_id}",
                    dept_name="Gujarat Police Traffic Wing",
                    latitude=23.0225,
                    longitude=72.5714,
                    plate_number=det.license_plate,
                    vehicle_type=det.vehicle_type or "Automobile",
                    vehicle_color="White",
                    confidence=det.confidence,
                    timestamp=det.timestamp,
                    snapshot_url=response.annotated_image_base64 or "",
                    is_watchlist_hit=det.is_watchlist_hit,
                    watchlist_category=det.watchlist_category
                ))

            # Persist to Supabase PostgreSQL (non-blocking)
            try:
                from app.services.supabase_service import get_supabase_service  # type: ignore # pyrefly: ignore [missing-import]
                sb = get_supabase_service()
                for det in response.detections:
                    sb.insert_license_plate_detection({
                        "id": f"DET-SB-{det.camera_id}-{int(datetime.now(timezone.utc).timestamp())}",
                        "camera_id": det.camera_id,
                        "plate_number": det.license_plate,
                        "confidence": det.confidence,
                        "timestamp": det.timestamp,
                        "bbox": det.bbox,
                        "image_reference": (response.annotated_image_base64[:50] + "...") if response.annotated_image_base64 else "",
                        "detection_type": "ANPR_LPR",
                        "vehicle_type": det.vehicle_type or "Automobile",
                        "is_watchlist_hit": det.is_watchlist_hit,
                        "watchlist_category": det.watchlist_category,
                        "watchlist_severity": det.watchlist_severity
                    })
            except Exception as sb_err:
                print(f"[LPR Router] Supabase persistence notice: {sb_err}")

            # Audit logging
            AUDIT_LOGS.append(AuditLog(
                id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
                camera_id=camera_id,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                user_id="SYSTEM-LPR",
                user_name="Intel OpenVINO LPR Service",
                role="AI_ENGINE",
                action_type="LPR_INFERENCE",
                previous_state=None,
                new_state=f"Detected {len(response.detections)} plate(s)",
                justification=f"LPR Processed image on {camera_id}: {[d.license_plate for d in response.detections]}",
                client_ip="127.0.0.1"
            ))
        except Exception as e:
            # Non-blocking platform telemetry hook
            print(f"[LPR Router] Telemetry hook warning: {e}")

    return response

@router.post("/process-video", response_model=LprVideoResponse)
async def process_video_for_lpr(
    file: UploadFile = File(...),
    camera_id: str = Form("CAM-ANPR-01"),
    sample_fps: float = Form(2.0),
    max_frames: int = Form(100)
):
    """
    Process an uploaded video clip frame-by-frame at a sampled rate.
    Returns chronological detections and list of unique identified plates.
    """
    pipeline = get_lpr_pipeline()
    suffix = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        shutil.copyfileobj(file.file, tmp)

    try:
        response = pipeline.process_video_file(
            video_path=tmp_path,
            camera_id=camera_id,
            sample_fps=sample_fps,
            max_frames=max_frames
        )
        return response
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

@router.get("/sample-demo", response_model=LprImageResponse)
def run_sample_demo():
    """
    Execute LPR on the sample ParkingVideo.mp4 frame bundled with Intel Edge AI resources.
    Returns detection coordinates and recognized plate '9MRM624'.
    """
    pipeline = get_lpr_pipeline()
    sample_video = SAMPLES_DIR / "ParkingVideo.mp4"
    if not sample_video.exists():
        ensure_models_available()

    sample_frame_path = SAMPLES_DIR / "sample_frame.jpg"
    if not sample_frame_path.exists() and sample_video.exists():
        import cv2  # type: ignore # pyrefly: ignore [missing-import]
        cap = cv2.VideoCapture(str(sample_video))
        ret, frame = cap.read()
        cap.release()
        if ret:
            cv2.imwrite(str(sample_frame_path), frame)

    if not sample_frame_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Sample demonstration frame could not be prepared."
        )

    with open(sample_frame_path, "rb") as f:
        img_bytes = f.read()

    return pipeline.process_image_bytes(
        img_bytes,
        camera_id="CAM-INTEL-DEMO",
        return_annotated=True
    )

@router.post("/download-models")
def download_models_endpoint():
    """Trigger programmatic verification and download of Intel IR models."""
    res = ensure_models_available(force_download=False)
    pipeline = get_lpr_pipeline()
    pipeline.initialize()
    return {"status": "SUCCESS", "details": res}
