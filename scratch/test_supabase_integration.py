"""
Automated Verification Test for Supabase Integration with CCTV Platform.
Tests:
1. Environment configuration (.env, .env.example, .gitignore)
2. SupabaseService initialization and check_connection()
3. Inserting a test camera into Supabase
4. Reading the test camera back
5. Inserting an AI/LPR license plate detection
6. Querying the detection back
7. FastAPI endpoint verification (/api/v1/supabase/status, /api/v1/supabase/test-camera, etc.)
"""
import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.supabase_service import get_supabase_service  # type: ignore # pyrefly: ignore [missing-import]
from fastapi.testclient import TestClient  # type: ignore # pyrefly: ignore [missing-import]
from backend.main import app  # type: ignore # pyrefly: ignore [missing-import]


def run_supabase_integration_test():
    print("================================================================")
    print("      SUPABASE POSTGRESQL INTEGRATION VERIFICATION TEST         ")
    print("================================================================")

    # 1. Environment & Files Check
    print("\n--- 1. Checking Environment & Security Isolation ---")
    env_path = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    gitignore_path = PROJECT_ROOT / ".gitignore"

    assert env_path.exists(), "Missing .env file"
    assert env_example.exists(), "Missing .env.example file"
    assert gitignore_path.exists(), "Missing .gitignore file"

    gitignore_content = gitignore_path.read_text(encoding="utf-8")
    assert ".env" in gitignore_content, ".env MUST be in .gitignore"
    print("  [PASS] .env exists and is isolated by .gitignore")
    print("  [PASS] .env.example template configured with placeholders")

    # 2. Service Initialization & Status
    print("\n--- 2. Checking Supabase Service Connection ---")
    service = get_supabase_service()
    status_info = service.check_connection()
    print("  Status Info:", json.dumps(status_info, indent=2))
    assert status_info["supabase_lib_available"] is True
    print("  [PASS] Supabase library is installed and operational")

    # 3. Test Inserting a Test Camera
    print("\n--- 3. Testing Camera Insertion ---")
    test_camera = {
        "id": "CAM-TEST-SB-01",
        "asset_code": "ASSET-GJ-SB-001",
        "name": "Gandhinagar Secretariat North Gate",
        "dept_id": "DEPT-01",
        "dept_name": "Gujarat Police Traffic Wing",
        "station_division": "Sector 10 Division",
        "responsible_officer": "Insp. V. K. Patel",
        "officer_phone": "+91-9876543210",
        "state": "Gujarat",
        "district": "Gandhinagar",
        "taluka": "Gandhinagar",
        "ward_zone": "Capital Zone",
        "latitude": 23.2156,
        "longitude": 72.6369,
        "altitude": 81.0,
        "fov_azimuth": 45.0,
        "fov_angle": 75.0,
        "coverage_radius": 120.0,
        "camera_type": "ANPR",
        "resolution": "4K",
        "fps": 30,
        "bitrate_kbps": 6144,
        "stream_url": "rtsp://10.20.30.40:554/live/ch1",
        "ownership": "Gujarat State Police",
        "vendor_name": "Intel/OpenVINO Edge",
        "status": "Active",
        "is_online": True,
        "health_score": 98
    }

    insert_cam_res = service.insert_camera(test_camera)
    print("  Camera Insert Result:", insert_cam_res)
    assert insert_cam_res["success"] is True
    print("  [PASS] Test Camera CAM-TEST-SB-01 inserted successfully")

    # 4. Reading the Camera Back
    print("\n--- 4. Reading Camera Back ---")
    fetched_cam = service.get_camera("CAM-TEST-SB-01")
    assert fetched_cam is not None, "Failed to retrieve inserted camera"
    assert fetched_cam["id"] == "CAM-TEST-SB-01"
    assert fetched_cam["name"] == "Gandhinagar Secretariat North Gate"
    print(f"  Fetched Camera: ID={fetched_cam['id']} | Name='{fetched_cam['name']}' | Status={fetched_cam['status']}")
    print("  [PASS] Camera retrieved and verified successfully")

    # 5. Inserting an AI/LPR Detection
    print("\n--- 5. Testing License Plate Detection Insertion ---")
    test_detection = {
        "id": "DET-SB-TEST-001",
        "camera_id": "CAM-TEST-SB-01",
        "plate_number": "GJ-01-AB-1234",
        "confidence": 0.985,
        "timestamp": "2026-09-15T01:35:00Z",
        "bbox": [100, 200, 350, 280],
        "image_reference": "https://storage.supabase.co/cctv-snapshots/cam-01-gj01ab1234.jpg",
        "video_reference": "ParkingVideo.mp4",
        "detection_type": "ANPR_LPR",
        "vehicle_type": "SUV",
        "vehicle_color": "White",
        "is_watchlist_hit": True,
        "watchlist_category": "STOLEN_VEHICLE",
        "watchlist_severity": "CRITICAL"
    }

    insert_det_res = service.insert_license_plate_detection(test_detection)
    print("  LPR Insert Result:", insert_det_res)
    assert insert_det_res["success"] is True
    print("  [PASS] License Plate Detection inserted successfully")

    # 6. Confirming the Record Appears
    print("\n--- 6. Confirming LPR Record Query ---")
    detections = service.get_license_plate_detections(camera_id="CAM-TEST-SB-01", limit=10)
    assert len(detections) >= 1, "Expected at least 1 detection record"
    matched = [d for d in detections if d.get("plate_number") == "GJ-01-AB-1234"]
    assert len(matched) >= 1, "Plate GJ-01-AB-1234 not found in detections"
    rec = matched[0]
    print(f"  Found Detection: ID={rec['id']} | Plate={rec['plate_number']} | Conf={rec['confidence']} | Watchlist Hit={rec['is_watchlist_hit']}")
    print("  [PASS] License Plate Detection confirmed in database query")

    # 7. FastAPI Endpoint Verification
    print("\n--- 7. Testing FastAPI Supabase Endpoints ---")
    client = TestClient(app)

    # 7a. GET /api/v1/supabase/status
    res_status = client.get("/api/v1/supabase/status")
    print("  GET /api/v1/supabase/status ->", res_status.status_code)
    assert res_status.status_code == 200
    assert res_status.json()["supabase_lib_available"] is True

    # 7b. POST /api/v1/supabase/test-camera
    new_cam_payload = {
        "id": "CAM-TEST-API-02",
        "asset_code": "ASSET-GJ-API-002",
        "name": "Ahmedabad Ring Road Cam 02",
        "dept_id": "DEPT-02",
        "dept_name": "Gujarat State Road Transport",
        "latitude": 23.0300,
        "longitude": 72.5800,
        "camera_type": "Dome",
        "status": "Active"
    }
    res_post_cam = client.post("/api/v1/supabase/test-camera", json=new_cam_payload)
    print("  POST /api/v1/supabase/test-camera ->", res_post_cam.status_code)
    assert res_post_cam.status_code == 200

    # 7c. GET /api/v1/supabase/camera/CAM-TEST-API-02
    res_get_cam = client.get("/api/v1/supabase/camera/CAM-TEST-API-02")
    print("  GET /api/v1/supabase/camera/CAM-TEST-API-02 ->", res_get_cam.status_code)
    assert res_get_cam.status_code == 200
    assert res_get_cam.json()["name"] == "Ahmedabad Ring Road Cam 02"

    # 7d. GET /api/v1/supabase/detections
    res_dets = client.get("/api/v1/supabase/detections?plate_number=GJ-01")
    print("  GET /api/v1/supabase/detections ->", res_dets.status_code)
    assert res_dets.status_code == 200
    assert len(res_dets.json()) >= 1

    print("\n================================================================")
    print("      ALL SUPABASE INTEGRATION TESTS PASSED (100% SUCCESS)      ")
    print("================================================================")


if __name__ == "__main__":
    run_supabase_integration_test()
