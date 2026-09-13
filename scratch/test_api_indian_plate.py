import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # type: ignore
import numpy as np  # type: ignore
from fastapi.testclient import TestClient  # type: ignore # pyrefly: ignore [missing-import]
from backend.main import app  # type: ignore # pyrefly: ignore [missing-import]

client = TestClient(app)

def test_indian_plate_api():
    print("--- Testing API with Watchlist Indian Plate 'GJ-01-AB-1234' ---")
    # Generate plate crop for GJ-01-AB-1234
    crop = np.full((60, 260, 3), 255, dtype=np.uint8)
    cv2.rectangle(crop, (0, 0), (259, 59), (0, 0, 0), 2)
    cv2.putText(crop, "GJ01AB1234", (14, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)

    _, buf = cv2.imencode(".jpg", crop)
    files = {"file": ("plate_gj01.jpg", buf.tobytes(), "image/jpeg")}
    data = {"camera_id": "CAM-0012", "annotate": "true"}

    res = client.post("/api/v1/ai/lpr/process-image", files=files, data=data)
    print("Status code:", res.status_code)
    data = res.json()
    print("Response JSON:")
    for d in data["detections"]:
        print(f"  Plate: {d['license_plate']}")
        print(f"  Confidence: {d['confidence']}")
        print(f"  Watchlist Hit: {d['is_watchlist_hit']}")
        print(f"  Category: {d['watchlist_category']}")
        print(f"  Severity: {d['watchlist_severity']}")
        print(f"  BBox: {d['bbox']}")

    assert res.status_code == 200
    assert len(data["detections"]) > 0
    assert "GJ01AB1234" in data["detections"][0]["license_plate"]
    assert data["detections"][0]["is_watchlist_hit"] is True
    print("\nSUCCESS: Indian plate correctly detected, recognized, and matched with CCTV Watchlist!")

if __name__ == "__main__":
    test_indian_plate_api()
