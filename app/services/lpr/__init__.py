"""
Intel OpenVINO License Plate Recognition (LPR) Service Module.
"""
from .schemas import (  # type: ignore # pyrefly: ignore [missing-import]
    LprDetectionResult,
    LprImageResponse,
    LprVideoResponse,
    LprVideoFrameDetection,
    LprStatusResponse
)
from .detector import OpenVinoYoloV8Detector  # type: ignore # pyrefly: ignore [missing-import]
from .recognizer import OpenVinoPaddleOcrRecognizer  # type: ignore # pyrefly: ignore [missing-import]
from .pipeline import LprPipeline, get_lpr_pipeline  # type: ignore # pyrefly: ignore [missing-import]

__all__ = [
    "LprDetectionResult",
    "LprImageResponse",
    "LprVideoResponse",
    "LprVideoFrameDetection",
    "LprStatusResponse",
    "OpenVinoYoloV8Detector",
    "OpenVinoPaddleOcrRecognizer",
    "LprPipeline",
    "get_lpr_pipeline"
]
