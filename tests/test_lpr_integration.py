"""
Unit and Integration Tests for Intel OpenVINO License Plate Recognition (LPR) Module.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # type: ignore
import cv2  # type: ignore
import numpy as np  # type: ignore
from fastapi.testclient import TestClient  # type: ignore # pyrefly: ignore [missing-import]

from backend.main import app, WATCHLIST  # type: ignore # pyrefly: ignore [missing-import]
from app.services.lpr import get_lpr_pipeline, LprPipeline  # type: ignore # pyrefly: ignore [missing-import]
from app.services.lpr.schemas import LprDetectionResult  # type: ignore # pyrefly: ignore [missing-import]

client = TestClient(app)

def test_lpr_status_endpoint():
    """Verify LPR engine status endpoint reports operational state and loaded models."""
    response = client.get("/api/v1/ai/lpr/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service_status"] == "OPERATIONAL"
    assert data["openvino_available"] is True
    assert data["models_ready"] is True
    assert data["detector_model_loaded"] is True
    assert data["recognizer_model_loaded"] is True
    assert "CPU" in data["devices_available"]

def test_lpr_sample_demo_endpoint():
    """Verify Intel sample demo frame detects plate '9MRM624' with high confidence."""
    response = client.get("/api/v1/ai/lpr/sample-demo")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_plates_found"] >= 1
    
    detected_plates = [d["license_plate"] for d in data["detections"]]
    assert "9MRM624" in detected_plates
    
    det = next(d for d in data["detections"] if d["license_plate"] == "9MRM624")
    assert det["confidence"] >= 0.85
    assert len(det["bbox"]) == 4
    # Coordinates in ParkingVideo.mp4 around [976, 453, 1022, 469]
    x1, y1, x2, y2 = det["bbox"]
    assert 900 <= x1 <= 1050
    assert 400 <= y1 <= 500

def test_lpr_process_image_upload():
    """Test image upload processing via FastAPI multipart form endpoint."""
    pipeline = get_lpr_pipeline()
    # Create test plate crop for GJ-05-XY-9876
    crop = np.full((60, 260, 3), 255, dtype=np.uint8)
    cv2.rectangle(crop, (0, 0), (259, 59), (0, 0, 0), 2)
    cv2.putText(crop, "GJ05XY9876", (14, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)

    _, buf = cv2.imencode(".jpg", crop)
    files = {"file": ("test_plate.jpg", buf.tobytes(), "image/jpeg")}
    data = {"camera_id": "CAM-0044", "annotate": "true"}

    response = client.post("/api/v1/ai/lpr/process-image", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert len(res_data["detections"]) >= 1

    det = res_data["detections"][0]
    assert "GJ05XY9876" in det["license_plate"]
    assert det["confidence"] >= 0.90
    assert det["camera_id"] == "CAM-0044"
    assert det["is_watchlist_hit"] is True
    assert det["watchlist_category"] == "Wanted Suspect"

def test_lpr_clean_plate_no_watchlist_hit():
    """Verify non-flagged plate does not falsely trigger watchlist alarm."""
    crop = np.full((60, 260, 3), 255, dtype=np.uint8)
    cv2.rectangle(crop, (0, 0), (259, 59), (0, 0, 0), 2)
    cv2.putText(crop, "GJ99ZZ1111", (14, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)

    _, buf = cv2.imencode(".jpg", crop)
    files = {"file": ("clean_plate.jpg", buf.tobytes(), "image/jpeg")}
    data = {"camera_id": "CAM-0089", "annotate": "true"}

    response = client.post("/api/v1/ai/lpr/process-image", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    det = res_data["detections"][0]
    assert det["is_watchlist_hit"] is False
    assert det["watchlist_category"] is None
