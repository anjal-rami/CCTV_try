"""
Pydantic schemas for License Plate Recognition (LPR) Service.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field  # type: ignore # pyrefly: ignore [missing-import]

class BoundingBox(BaseModel):
    x1: int = Field(default=0, description="Left coordinate")
    y1: int = Field(default=0, description="Top coordinate")
    x2: int = Field(default=0, description="Right coordinate")
    y2: int = Field(default=0, description="Bottom coordinate")

    def to_list(self) -> List[int]:
        return [self.x1, self.y1, self.x2, self.y2]

class LprDetectionResult(BaseModel):
    camera_id: str = Field(default="", description="Camera identifier")
    timestamp: str = Field(default="", description="ISO 8601 formatted timestamp")
    license_plate: str = Field(default="", description="Recognized plate characters")
    confidence: float = Field(default=0.0, description="Detection and OCR combined confidence score")
    bbox: List[int] = Field(default_factory=list, description="Bounding box [x1, y1, x2, y2]")
    vehicle_type: Optional[str] = Field(default="Vehicle", description="Predicted or inferred vehicle class")
    is_watchlist_hit: bool = Field(default=False, description="Whether plate matched the law enforcement watchlist")
    watchlist_category: Optional[str] = Field(default=None, description="Category if matched (e.g. Stolen Vehicle)")
    watchlist_severity: Optional[str] = Field(default=None, description="Severity if matched (e.g. Critical)")
    processing_time_ms: float = Field(default=0.0, description="End-to-end inference latency in milliseconds")
    device_used: Optional[str] = Field(default="CPU", description="Inference device used (CPU, GPU, NPU)")

class LprImageResponse(BaseModel):
    success: bool = True
    detections: List[LprDetectionResult] = Field(default_factory=list)
    total_plates_found: int = 0
    image_width: int = 0
    image_height: int = 0
    annotated_image_base64: Optional[str] = None
    processing_time_ms: float = 0.0
    message: Optional[str] = None

class LprVideoFrameDetection(BaseModel):
    frame_index: int = 0
    timestamp_offset_sec: float = 0.0
    detections: List[LprDetectionResult] = Field(default_factory=list)

class LprVideoResponse(BaseModel):
    success: bool = True
    video_name: str = ""
    total_frames_analyzed: int = 0
    frames_with_detections: int = 0
    unique_plates: List[str] = Field(default_factory=list)
    timeline: List[LprVideoFrameDetection] = Field(default_factory=list)
    total_processing_time_sec: float = 0.0
    message: Optional[str] = None

class LprStatusResponse(BaseModel):
    service_status: str = "INITIALIZING"
    openvino_available: bool = False
    openvino_version: Optional[str] = None
    devices_available: List[str] = Field(default_factory=list)
    active_device: str = "CPU"
    detector_model_loaded: bool = False
    detector_model_path: Optional[str] = None
    recognizer_model_loaded: bool = False
    recognizer_model_path: Optional[str] = None
    models_ready: bool = False
