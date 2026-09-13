"""
Test PP-OCRv4 standalone on Indian / Gujarat plate crops
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2  # type: ignore # pyrefly: ignore [missing-import]
import numpy as np  # type: ignore # pyrefly: ignore [missing-import]
from app.services.lpr import get_lpr_pipeline  # type: ignore # pyrefly: ignore [missing-import]

pipeline = get_lpr_pipeline()

def test_ocr_on_indian_crops():
    print("Testing PP-OCRv4 recognizer directly on Indian Plate crops:")
    samples = [
        ("GJ01AB1234", "GJ-01-AB-1234 single line"),
        ("GJ05XY9876", "GJ-05-XY-9876 Surat"),
        ("GJ06AX9999", "GJ-06-AX-9999 Vadodara Commercial"),
        ("MH12DE1432", "MH-12-DE-1432 Inter-state"),
    ]

    assert pipeline.recognizer is not None, "Pipeline recognizer must be initialized"

    for plate_txt, desc in samples:
        # Create clear plate crop (48x200)
        crop = np.full((60, 240, 3), 255, dtype=np.uint8)
        cv2.rectangle(crop, (0, 0), (239, 59), (0, 0, 0), 2)
        cv2.putText(crop, plate_txt, (12, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2, cv2.LINE_AA)

        rec_text, conf = pipeline.recognizer.recognize(crop)
        print(f"[{desc}] Target: {plate_txt} => Recognized: '{rec_text}', Conf: {conf}")

if __name__ == "__main__":
    test_ocr_on_indian_crops()
