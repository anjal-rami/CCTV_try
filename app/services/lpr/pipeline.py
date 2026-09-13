"""
End-to-End License Plate Recognition Pipeline Orchestrator.
Combines YOLOv8 Plate Detector with PaddleOCR PP-OCRv4 Recognizer.
"""
import os
import cv2  # type: ignore # pyrefly: ignore [missing-import]
import time
import base64
import numpy as np  # type: ignore # pyrefly: ignore [missing-import]
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .schemas import (  # type: ignore # pyrefly: ignore [missing-import]
    LprDetectionResult,
    LprImageResponse,
    LprVideoResponse,
    LprVideoFrameDetection,
    LprStatusResponse
)
from .detector import OpenVinoYoloV8Detector, OPENVINO_AVAILABLE  # type: ignore # pyrefly: ignore [missing-import]
from .recognizer import OpenVinoPaddleOcrRecognizer  # type: ignore # pyrefly: ignore [missing-import]
from .model_downloader import ensure_models_available, MODELS_DIR  # type: ignore # pyrefly: ignore [missing-import]

class LprPipeline:
    _instance = None

    def __init__(self, device: str = "CPU", auto_init: bool = True):
        self.device = device
        self.detector: Optional[OpenVinoYoloV8Detector] = None
        self.recognizer: Optional[OpenVinoPaddleOcrRecognizer] = None
        self.models_ready = False
        self.active_device = device
        self.openvino_version = None

        if auto_init:
            self.initialize()

    @classmethod
    def get_instance(cls, device: str = "CPU") -> "LprPipeline":
        if cls._instance is None:
            cls._instance = LprPipeline(device=device)
        return cls._instance

    def initialize(self) -> bool:
        """Download assets and initialize OpenVINO models."""
        try:
            if OPENVINO_AVAILABLE:
                import openvino as ov  # type: ignore # pyrefly: ignore [missing-import]
                self.openvino_version = ov.__version__

            model_info = ensure_models_available()
            if model_info.get("status") != "READY":
                print(f"[LPR Pipeline] Models not fully available: {model_info}")
                return False

            dict_path = MODELS_DIR / "ppocr_keys_v1.txt"
            if not dict_path.exists():
                import urllib.request
                url = "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/ppocr_keys_v1.txt"
                urllib.request.urlretrieve(url, dict_path)

            self.detector = OpenVinoYoloV8Detector(
                model_path=model_info["detector_xml"],
                device=self.device
            )
            self.recognizer = OpenVinoPaddleOcrRecognizer(
                model_path=model_info["ocr_xml"],
                dict_path=str(dict_path),
                device=self.device
            )

            self.models_ready = bool(
                self.detector and self.detector.is_loaded and
                self.recognizer and self.recognizer.is_loaded
            )
            if self.detector and self.detector.is_loaded:
                self.active_device = self.detector.device

            print(f"[LPR Pipeline] Initialized successfully. Models ready: {self.models_ready} on {self.active_device}")
            return self.models_ready
        except Exception as e:
            print(f"[LPR Pipeline] Error during initialization: {e}")
            self.models_ready = False
            return False

    def get_status(self) -> LprStatusResponse:
        """Get telemetry and device status of the LPR engine."""
        devices = []
        if OPENVINO_AVAILABLE:
            try:
                import openvino as ov  # type: ignore # pyrefly: ignore [missing-import]
                devices = ov.Core().available_devices
            except Exception:
                devices = ["CPU"]

        det_loaded = bool(self.detector and self.detector.is_loaded)
        rec_loaded = bool(self.recognizer and self.recognizer.is_loaded)

        return LprStatusResponse(
            service_status="OPERATIONAL" if (det_loaded and rec_loaded) else "DEGRADED",
            openvino_available=OPENVINO_AVAILABLE,
            openvino_version=self.openvino_version,
            devices_available=devices,
            active_device=self.active_device,
            detector_model_loaded=det_loaded,
            detector_model_path=self.detector.model_path if self.detector else None,
            recognizer_model_loaded=rec_loaded,
            recognizer_model_path=self.recognizer.model_path if self.recognizer else None,
            models_ready=det_loaded and rec_loaded
        )

    def check_watchlist(self, plate: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if plate matches any watchlist record in the CCTV database."""
        try:
            from backend.main import WATCHLIST  # type: ignore # pyrefly: ignore [missing-import]
            norm_plate = plate.replace("-", "").replace(" ", "").upper()
            for w in WATCHLIST:
                w_plate = w.plate_number.replace("-", "").replace(" ", "").upper()
                if norm_plate and (norm_plate == w_plate or norm_plate in w_plate or w_plate in norm_plate):
                    return True, w.category, w.severity
        except Exception:
            pass
        return False, None, None

    def process_frame(
        self,
        img: np.ndarray,
        camera_id: str = "CAM-ANPR-01",
        timestamp: Optional[str] = None
    ) -> List[LprDetectionResult]:
        """
        Run detection and OCR on a single frame (OpenCV BGR numpy array).
        Returns list of structured detection results.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        if not self.models_ready or self.detector is None or self.recognizer is None:
            # Try lazy initialization
            if not self.initialize() or self.detector is None or self.recognizer is None:
                return []

        start_time = time.perf_counter()
        raw_detections = self.detector.detect(img)
        results = []

        h0, w0 = img.shape[:2]
        margin = 4

        for det in raw_detections:
            x1, y1, x2, y2 = det["bbox"]
            det_conf = det["confidence"]

            # Crop with safe margin
            x1_m = max(0, x1 - margin)
            y1_m = max(0, y1 - margin)
            x2_m = min(w0, x2 + margin)
            y2_m = min(h0, y2 + margin)

            crop = img[y1_m:y2_m, x1_m:x2_m]
            if crop.size == 0:
                continue

            plate_text, ocr_conf = self.recognizer.recognize(crop)
            if not plate_text:
                continue

            # Combined confidence score (geometric mean)
            combined_conf = round(float(np.sqrt(det_conf * max(ocr_conf, 0.1))), 4)
            is_hit, category, severity = self.check_watchlist(plate_text)

            proc_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            results.append(LprDetectionResult(
                camera_id=camera_id,
                timestamp=timestamp,
                license_plate=plate_text,
                confidence=combined_conf,
                bbox=[x1, y1, x2, y2],
                vehicle_type="Automobile",
                is_watchlist_hit=is_hit,
                watchlist_category=category,
                watchlist_severity=severity,
                processing_time_ms=proc_ms,
                device_used=self.active_device
            ))

        if not raw_detections and h0 > 15 and w0 > 40:
            # Fallback: The uploaded image itself may be a cropped plate image or tight CCTV ROI
            aspect_ratio = w0 / float(max(h0, 1))
            if 1.2 <= aspect_ratio <= 7.0:
                plate_text, ocr_conf = self.recognizer.recognize(img)
                if plate_text and len(plate_text) >= 4 and ocr_conf >= 0.5:
                    is_hit, category, severity = self.check_watchlist(plate_text)
                    proc_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                    results.append(LprDetectionResult(
                        camera_id=camera_id,
                        timestamp=timestamp,
                        license_plate=plate_text,
                        confidence=round(float(ocr_conf), 4),
                        bbox=[2, 2, w0 - 2, h0 - 2],
                        vehicle_type="Cropped Plate ROI",
                        is_watchlist_hit=is_hit,
                        watchlist_category=category,
                        watchlist_severity=severity,
                        processing_time_ms=proc_ms,
                        device_used=self.active_device
                    ))

        return results

    def annotate_frame(self, img: np.ndarray, detections: List[LprDetectionResult]) -> np.ndarray:
        """Draw aesthetic bounding boxes and plate labels onto the image."""
        out = img.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = (0, 0, 255) if det.is_watchlist_hit else (0, 220, 0) # Red if hit, Green otherwise

            # Draw glowing bounding box
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

            label = f"{det.license_plate} ({int(det.confidence * 100)}%)"
            if det.is_watchlist_hit:
                label += f" ! [{det.watchlist_category}]"

            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
            cv2.rectangle(out, (x1, max(0, y1 - lh - 10)), (x1 + lw + 8, y1), color, -1)
            cv2.putText(
                out, label, (x1 + 4, max(lh + 4, y1 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA
            )

        return out

    def process_image_bytes(
        self,
        image_bytes: bytes,
        camera_id: str = "CAM-ANPR-01",
        return_annotated: bool = True
    ) -> LprImageResponse:
        """Process image file bytes and return structured results with optional annotated base64 image."""
        t0 = time.perf_counter()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return LprImageResponse(
                success=False,
                detections=[],
                total_plates_found=0,
                image_width=0,
                image_height=0,
                processing_time_ms=0.0,
                message="Failed to decode image from provided bytes"
            )

        h, w = img.shape[:2]
        detections = self.process_frame(img, camera_id=camera_id)

        annotated_b64 = None
        if return_annotated:
            annotated = self.annotate_frame(img, detections)
            ret_enc, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret_enc and buf is not None:
                annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("utf-8")

        total_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        return LprImageResponse(
            success=True,
            detections=detections,
            total_plates_found=len(detections),
            image_width=w,
            image_height=h,
            annotated_image_base64=annotated_b64,
            processing_time_ms=total_time_ms,
            message="License plate detection completed successfully"
        )

    def process_video_file(
        self,
        video_path: str,
        camera_id: str = "CAM-ANPR-01",
        sample_fps: float = 2.0,
        max_frames: int = 150
    ) -> LprVideoResponse:
        """Process video file at sample intervals and return aggregated timeline."""
        t0 = time.perf_counter()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return LprVideoResponse(
                success=False,
                video_name=Path(video_path).name,
                total_frames_analyzed=0,
                frames_with_detections=0,
                unique_plates=[],
                timeline=[],
                total_processing_time_sec=0.0,
                message=f"Could not open video file: {video_path}"
            )

        video_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_step = max(1, int(round(video_fps / sample_fps)))

        timeline = []
        unique_plates_set = set()
        frames_analyzed = 0
        frame_idx = 0

        while cap.isOpened() and frames_analyzed < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_step == 0:
                time_offset = round(frame_idx / video_fps, 2)
                dets = self.process_frame(frame, camera_id=camera_id)
                frames_analyzed += 1

                if dets:
                    timeline.append(LprVideoFrameDetection(
                        frame_index=frame_idx,
                        timestamp_offset_sec=time_offset,
                        detections=dets
                    ))
                    for d in dets:
                        unique_plates_set.add(d.license_plate)

            frame_idx += 1

        cap.release()
        total_time_sec = round(time.perf_counter() - t0, 2)

        return LprVideoResponse(
            success=True,
            video_name=Path(video_path).name,
            total_frames_analyzed=frames_analyzed,
            frames_with_detections=len(timeline),
            unique_plates=sorted(list(unique_plates_set)),
            timeline=timeline,
            total_processing_time_sec=total_time_sec,
            message="Video LPR processing completed successfully"
        )

def get_lpr_pipeline() -> LprPipeline:
    return LprPipeline.get_instance()
