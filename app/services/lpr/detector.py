"""
OpenVINO YOLOv8 License Plate Detector Module.
Performs vehicle license plate localization on CPU, GPU, or NPU.
"""
import os
import cv2  # type: ignore # pyrefly: ignore [missing-import]
import numpy as np  # type: ignore # pyrefly: ignore [missing-import]
from typing import List, Tuple, Dict, Any

try:
    import openvino as ov  # type: ignore # pyrefly: ignore [missing-import]
    OPENVINO_AVAILABLE = True
except ImportError:
    ov = None
    OPENVINO_AVAILABLE = False

class OpenVinoYoloV8Detector:
    def __init__(
        self,
        model_path: str,
        device: str = "CPU",
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        target_size: Tuple[int, int] = (640, 640)
    ):
        self.model_path = model_path
        self.device = device
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.target_size = target_size
        self.core = None
        self.compiled_model = None
        self.is_loaded = False

        if OPENVINO_AVAILABLE and os.path.exists(model_path):
            self._load_model()

    def _load_model(self):
        if ov is None:
            return
        try:
            self.core = ov.Core()
            available = self.core.available_devices
            # Graceful fallback to CPU if requested device is not present
            target_device = self.device if self.device in available else "CPU"
            
            model = self.core.read_model(self.model_path)
            self.compiled_model = self.core.compile_model(model, target_device)
            self.device = target_device
            self.is_loaded = True
            print(f"[LPR Detector] Loaded YOLOv8 detector on device: {self.device}")
        except Exception as e:
            print(f"[LPR Detector] Failed to load OpenVINO model: {e}")
            self.is_loaded = False

    def preprocess(self, img: np.ndarray) -> Tuple[np.ndarray, float, Tuple[float, float]]:
        """Letterbox resize image to target_size maintaining aspect ratio with border padding."""
        h0, w0 = img.shape[:2]
        tw, th = self.target_size

        r = min(tw / w0, th / h0)
        new_unpad = (int(round(w0 * r)), int(round(h0 * r)))
        dw, dh = (tw - new_unpad[0]) / 2, (th - new_unpad[1]) / 2

        resized = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        padded = cv2.copyMakeBorder(
            resized, top, bottom, left, right,
            cv2.BORDER_CONSTANT, value=(114, 114, 114)
        )

        blob = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)[np.newaxis, ...]
        return blob, r, (dw, dh)

    def detect(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect license plates in an input image (BGR format).
        Returns list of detections with bbox [x1, y1, x2, y2] and confidence.
        """
        if not self.is_loaded or self.compiled_model is None:
            return []

        h0, w0 = img.shape[:2]
        blob, r, (dw, dh) = self.preprocess(img)

        # Run inference
        outputs = self.compiled_model([blob])
        raw_output = outputs[self.compiled_model.output(0)]

        # Raw output is [1, 5, 8400] -> transpose to [8400, 5]
        preds = np.squeeze(raw_output, axis=0)
        if preds.shape[0] == 5 and preds.shape[1] > 5:
            preds = preds.T

        scores = preds[:, 4]
        mask = scores >= self.conf_threshold
        filtered_preds = preds[mask]

        if len(filtered_preds) == 0:
            return []

        boxes = []
        confidences = []
        for p in filtered_preds:
            cx, cy, w, h, score = p[:5]
            x1 = (cx - w / 2.0 - dw) / r
            y1 = (cy - h / 2.0 - dh) / r
            x2 = (cx + w / 2.0 - dw) / r
            y2 = (cy + h / 2.0 - dh) / r

            # Clip to image boundaries
            x1 = max(0, min(w0 - 1, int(x1)))
            y1 = max(0, min(h0 - 1, int(y1)))
            x2 = max(0, min(w0 - 1, int(x2)))
            y2 = max(0, min(h0 - 1, int(y2)))

            if x2 > x1 and y2 > y1:
                boxes.append([x1, y1, x2 - x1, y2 - y1]) # xywh for cv2.dnn.NMSBoxes
                confidences.append(float(score))

        if not boxes:
            return []

        indices = cv2.dnn.NMSBoxes(boxes, confidences, self.conf_threshold, self.iou_threshold)
        results = []
        if len(indices) > 0:
            for idx in np.array(indices).flatten():
                x, y, w, h = boxes[int(idx)]
                results.append({
                    "bbox": [x, y, x + w, y + h],
                    "confidence": round(float(confidences[idx]), 4),
                    "label": "license_plate"
                })

        return results
