import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
from fastapi.testclient import TestClient  # type: ignore # pyrefly: ignore [missing-import]
from backend.main import app  # type: ignore # pyrefly: ignore [missing-import]

client = TestClient(app)

def test_lpr_endpoints():
    print("--- 1. Testing GET /api/v1/ai/lpr/status ---")
    res = client.get("/api/v1/ai/lpr/status")
    print("Status code:", res.status_code)
    status_data = res.json()
    print("Status response:", json.dumps(status_data, indent=2))
    assert res.status_code == 200
    assert status_data["models_ready"] is True

    print("\n--- 2. Testing GET /api/v1/ai/lpr/sample-demo ---")
    res_demo = client.get("/api/v1/ai/lpr/sample-demo")
    print("Sample demo status code:", res_demo.status_code)
    demo_data = res_demo.json()
    print("Total plates found:", demo_data["total_plates_found"])
    for d in demo_data["detections"]:
        print(f"  Camera: {d['camera_id']} | Plate: {d['license_plate']} | Conf: {d['confidence']} | BBox: {d['bbox']}")
    assert res_demo.status_code == 200
    assert demo_data["total_plates_found"] >= 1
    assert "9MRM624" in [d["license_plate"] for d in demo_data["detections"]]

    print("\n--- 3. Testing POST /api/v1/ai/lpr/process-image ---")
    with open("app/services/lpr/samples/sample_frame.jpg", "rb") as f:
        file_bytes = f.read()

    files = {"file": ("sample_frame.jpg", file_bytes, "image/jpeg")}
    data = {"camera_id": "CAM-GJ-TEST-01", "annotate": "true"}
    res_img = client.post("/api/v1/ai/lpr/process-image", files=files, data=data)
    print("Image upload status code:", res_img.status_code)
    img_data = res_img.json()
    print("Detections from uploaded image:", len(img_data["detections"]))
    for d in img_data["detections"]:
        print(f"  Plate: {d['license_plate']} | Conf: {d['confidence']} | Watchlist hit: {d['is_watchlist_hit']}")
    assert res_img.status_code == 200

    print("\nALL LPR API ENDPOINT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_lpr_endpoints()
