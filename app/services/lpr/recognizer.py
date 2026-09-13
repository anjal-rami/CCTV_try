"""
OpenVINO PaddleOCR PP-OCRv4 Character Recognizer Module.
Performs alphanumeric sequence recognition on cropped license plate regions.
"""
import os
import cv2  # type: ignore
import re
import numpy as np  # type: ignore
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

try:
    import openvino as ov  # type: ignore
    OPENVINO_AVAILABLE = True
except ImportError:
    ov = None
    OPENVINO_AVAILABLE = False

class OpenVinoPaddleOcrRecognizer:
    def __init__(
        self,
        model_path: str,
        dict_path: str,
        device: str = "CPU",
        target_height: int = 48,
        target_width: int = 192
    ):
        self.model_path = model_path
        self.dict_path = dict_path
        self.device = device
        self.target_height = target_height
        self.target_width = target_width
        self.core = None
        self.compiled_model = None
        self.char_dict: Dict[int, str] = {}
        self.is_loaded = False

        self._load_dictionary()
        if OPENVINO_AVAILABLE and os.path.exists(model_path):
            self._load_model()

    def _load_dictionary(self):
        """Load character map from ppocr_keys dictionary."""
        if not os.path.exists(self.dict_path):
            print(f"[LPR Recognizer] Character dictionary not found at {self.dict_path}")
            return

        with open(self.dict_path, "r", encoding="utf-8") as f:
            char_list = [line.strip("\r\n") for line in f]

        # PP-OCR Index mapping:
        # Index 0 is CTC blank token
        # Index 1 to len(char_list) are character vocabulary
        # Index len(char_list) + 1 is space ' '
        self.char_dict = {i + 1: char_list[i] for i in range(len(char_list))}
        self.char_dict[0] = ""
        self.char_dict[len(char_list) + 1] = " "
        print(f"[LPR Recognizer] Loaded character dictionary with {len(self.char_dict)} tokens")

    def _load_model(self):
        if ov is None:
            return
        try:
            self.core = ov.Core()
            available = self.core.available_devices
            target_device = self.device if self.device in available else "CPU"

            model = self.core.read_model(self.model_path)
            self.compiled_model = self.core.compile_model(model, target_device)
            self.device = target_device
            self.is_loaded = True
            print(f"[LPR Recognizer] Loaded PP-OCRv4 model on device: {self.device}")
        except Exception as e:
            print(f"[LPR Recognizer] Failed to load OpenVINO recognizer model: {e}")
            self.is_loaded = False

    def preprocess(self, crop: np.ndarray) -> np.ndarray:
        """Resize cropped plate to (target_height, target_width) and normalize."""
        crop_h, crop_w = crop.shape[:2]
        r = self.target_height / max(crop_h, 1)
        new_w = min(int(round(crop_w * r)), self.target_width)

        resized = cv2.resize(crop, (new_w, self.target_height), interpolation=cv2.INTER_LINEAR)
        padded = np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
        padded[:, :new_w] = resized

        blob = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        # Normalization for PP-OCRv4: (x / 255.0 - 0.5) / 0.5
        blob = (blob.astype(np.float32) / 255.0 - 0.5) / 0.5
        blob = blob.transpose(2, 0, 1)[np.newaxis, ...]
        return blob

    def recognize(self, crop: np.ndarray) -> Tuple[str, float]:
        """
        Recognize license plate text from cropped ROI.
        Returns: (recognized_plate_text, confidence_score)
        """
        if not self.is_loaded or self.compiled_model is None or crop.size == 0:
            return "", 0.0

        blob = self.preprocess(crop)
        outputs = self.compiled_model([blob])  # type: ignore
        raw_output = outputs[self.compiled_model.output(0)]  # type: ignore

        # Shape: [1, T, 6625]
        preds = np.squeeze(raw_output, axis=0) # [T, 6625]
        pred_indices = np.argmax(preds, axis=1)

        decoded_chars = []
        char_confs = []
        prev_idx = 0

        for t, idx in enumerate(pred_indices):
            # CTC rule: skip blank (0) and consecutive duplicates
            if idx != 0 and idx != prev_idx:
                ch = self.char_dict.get(idx, "")
                if ch:
                    decoded_chars.append(ch)
                    # The raw output from this model already represents softmax probabilities
                    char_confs.append(float(preds[t, idx]))
            prev_idx = idx

        raw_text = "".join(decoded_chars).strip()
        # Clean plate text (alphanumeric uppercase and hyphens)
        clean_text = re.sub(r"[^A-Za-z0-9\-]", "", raw_text).upper()
        avg_conf = float(np.mean(char_confs)) if char_confs else 0.0

        return clean_text, round(avg_conf, 4)
