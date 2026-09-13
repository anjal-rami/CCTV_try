"""
Empirical Evaluation of Intel OpenVINO LPR on Indian / Gujarat License Plates.
Tests single-line HSRP plates, two-line stacked plates, and font variations.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # type: ignore
import numpy as np  # type: ignore
from app.services.lpr import get_lpr_pipeline  # type: ignore

pipeline = get_lpr_pipeline()

def create_synthetic_car_with_plate(
    plate_text: str,
    two_line: bool = False,
    is_hsrp: bool = True,
    plate_bg_color: tuple = (245, 245, 245),
    text_color: tuple = (20, 20, 20)
) -> np.ndarray:
    """Create a realistic car front bumper test image with mounted license plate."""
    # 1280x720 scene
    img = np.full((720, 1280, 3), (70, 75, 80), dtype=np.uint8) # Dark car body
    # Car grill pattern
    cv2.rectangle(img, (340, 250), (940, 520), (30, 30, 30), -1)
    for y in range(270, 500, 20):
        cv2.line(img, (360, y), (920, y), (50, 50, 50), 2)

    # Plate dimensions
    if two_line:
        # Two-line plate (more square aspect ratio ~ 200x120)
        pw, ph = 220, 140
        px, py = 530, 350
        cv2.rectangle(img, (px, py), (px + pw, py + ph), plate_bg_color, -1)
        cv2.rectangle(img, (px, py), (px + pw, py + ph), (10, 10, 10), 3)

        lines = plate_text.split()
        l1 = lines[0] if len(lines) > 0 else plate_text[:4]
        l2 = " ".join(lines[1:]) if len(lines) > 1 else plate_text[4:]
        cv2.putText(img, l1, (px + 20, py + 55), cv2.FONT_HERSHEY_SIMPLEX, 1.3, text_color, 3, cv2.LINE_AA)
        cv2.putText(img, l2, (px + 20, py + 115), cv2.FONT_HERSHEY_SIMPLEX, 1.3, text_color, 3, cv2.LINE_AA)
    else:
        # Single-line rectangular plate (aspect ratio ~ 380x80)
        pw, ph = 380, 85
        px, py = 450, 380
        cv2.rectangle(img, (px, py), (px + pw, py + ph), plate_bg_color, -1)
        cv2.rectangle(img, (px, py), (px + pw, py + ph), (10, 10, 10), 3)

        offset_x = px + 20
        if is_hsrp:
            # Blue strip on left with IND
            cv2.rectangle(img, (px + 3, py + 3), (px + 45, py + ph - 3), (180, 50, 30), -1)
            cv2.putText(img, "IND", (px + 7, py + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            offset_x = px + 55

        clean_text = plate_text.replace("-", " ")
        cv2.putText(img, clean_text, (offset_x, py + 58), cv2.FONT_HERSHEY_SIMPLEX, 1.45, text_color, 3, cv2.LINE_AA)

    return img

def benchmark_indian_plates():
    test_cases = [
        {
            "name": "Case 1: Standard Gujarat Private Car (HSRP Single Line)",
            "plate": "GJ-01-AB-1234",
            "two_line": False,
            "is_hsrp": True,
            "bg": (245, 245, 245), # White
            "fg": (20, 20, 20)
        },
        {
            "name": "Case 2: Gujarat Commercial Taxi/Cab (Yellow Single Line)",
            "plate": "GJ-06-AX-9999",
            "two_line": False,
            "is_hsrp": True,
            "bg": (0, 215, 255), # Yellow
            "fg": (15, 15, 15)
        },
        {
            "name": "Case 3: Gujarat EV Electric Vehicle (Green Plate)",
            "plate": "GJ-27-EE-5001",
            "two_line": False,
            "is_hsrp": True,
            "bg": (40, 140, 40), # Green
            "fg": (250, 250, 250)
        },
        {
            "name": "Case 4: Gujarat Commercial Auto/Truck (Two-Line Stacked)",
            "plate": "GJ01 DE5555",
            "two_line": True,
            "is_hsrp": False,
            "bg": (0, 215, 255),
            "fg": (15, 15, 15)
        }
    ]

    print("================================================================================")
    print("EMPIRICAL BENCHMARK: INTEL OPENVINO LPR ON GUJARAT / INDIAN LICENSE PLATES")
    print("================================================================================")

    results = []
    for tc in test_cases:
        img = create_synthetic_car_with_plate(
            plate_text=tc["plate"],
            two_line=tc["two_line"],
            is_hsrp=tc["is_hsrp"],
            plate_bg_color=tc["bg"],
            text_color=tc["fg"]
        )

        dets = pipeline.process_frame(img, camera_id="CAM-GJ-EVAL")
        detected = len(dets) > 0
        rec_text = dets[0].license_plate if detected else "NOT_DETECTED"
        conf = dets[0].confidence if detected else 0.0
        bbox = dets[0].bbox if detected else []

        print(f"\n[{tc['name']}]")
        print(f"  Target Plate String : {tc['plate']}")
        print(f"  Plate Detected      : {'YES' if detected else 'NO'}")
        print(f"  Detected BBox       : {bbox}")
        print(f"  Recognized String   : {rec_text}")
        print(f"  Confidence Score    : {conf}")

        results.append({
            "test": tc["name"],
            "target": tc["plate"],
            "detected": detected,
            "recognized": rec_text,
            "conf": conf,
            "bbox": bbox
        })

    print("\n================================================================================")
    print("INDIAN PLATE SUITABILITY SUMMARY")
    print("================================================================================")
    return results

if __name__ == "__main__":
    benchmark_indian_plates()
