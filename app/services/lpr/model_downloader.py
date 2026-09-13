"""
Model Downloader and Asset Manager for Intel LPR Module.
Fetches YOLOv8 License Plate Detector & PaddleOCR PP-OCRv4 OpenVINO IR files.
"""
import os
import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional

MODELS_ZIP_URL = "https://github.com/open-edge-platform/edge-ai-resources/raw/main/models/license-plate-reader.zip"
SAMPLE_VIDEO_URL = "https://github.com/open-edge-platform/edge-ai-resources/raw/main/videos/ParkingVideo.mp4"

# Default directories
LPR_DIR = Path(__file__).resolve().parent
MODELS_DIR = LPR_DIR / "models"
SAMPLES_DIR = LPR_DIR / "samples"
EXTERNAL_REPO_DIR = Path("C:/Users/Admin/license-plate-recognition")

def find_existing_models() -> Optional[Dict[str, Path]]:
    """Scan candidate directories for existing OpenVINO IR model files."""
    candidate_dirs = [
        MODELS_DIR,
        EXTERNAL_REPO_DIR / "models",
        EXTERNAL_REPO_DIR / "models" / "yolov8_license_plate_detector" / "license-plate-reader" / "models",
        EXTERNAL_REPO_DIR
    ]

    for c_dir in candidate_dirs:
        if not c_dir.exists():
            continue
        
        det_xmls = list(c_dir.rglob("*yolov8n_retrained*.xml")) or list(c_dir.rglob("*retrained*.xml"))
        ocr_xmls = list(c_dir.rglob("*ch_PP-OCRv4_rec_infer*.xml"))

        if det_xmls and ocr_xmls:
            det_xml = det_xmls[0]
            det_bin = det_xml.with_suffix(".bin")
            ocr_xml = ocr_xmls[0]
            ocr_bin = ocr_xml.with_suffix(".bin")

            if det_bin.exists() and ocr_bin.exists():
                return {
                    "detector_xml": det_xml,
                    "detector_bin": det_bin,
                    "ocr_xml": ocr_xml,
                    "ocr_bin": ocr_bin
                }
    return None

def download_file(url: str, dest_path: Path, label: str = "asset") -> bool:
    """Download a file with user-friendly console progress output."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".download")
    
    print(f"[LPR Downloader] Downloading {label} from {url}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Intel-LPR-Integration/1.0"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=90) as response, open(temp_path, "wb") as out_file:
            shutil.copyfileobj(response, out_file)
        
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
        print(f"[LPR Downloader] Successfully downloaded {label} to {dest_path}")
        return True
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"[LPR Downloader] Failed to download {label}: {e}", file=sys.stderr)
        return False

def ensure_models_available(force_download: bool = False) -> Dict[str, Any]:
    """
    Ensure detector and recognizer IR files are locally available.
    Downloads and extracts them if not already present.
    """
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    existing = find_existing_models() if not force_download else None
    if existing:
        # If found in external folder, copy/symlink to local models dir for self-containment
        local_det_xml = MODELS_DIR / "yolov8n_retrained.xml"
        local_det_bin = MODELS_DIR / "yolov8n_retrained.bin"
        local_ocr_xml = MODELS_DIR / "ch_PP-OCRv4_rec_infer.xml"
        local_ocr_bin = MODELS_DIR / "ch_PP-OCRv4_rec_infer.bin"

        if not local_det_xml.exists():
            shutil.copy2(existing["detector_xml"], local_det_xml)
            shutil.copy2(existing["detector_bin"], local_det_bin)
        if not local_ocr_xml.exists():
            shutil.copy2(existing["ocr_xml"], local_ocr_xml)
            shutil.copy2(existing["ocr_bin"], local_ocr_bin)

        sample_video = ensure_sample_video()
        return {
            "status": "READY",
            "detector_xml": str(local_det_xml),
            "detector_bin": str(local_det_bin),
            "ocr_xml": str(local_ocr_xml),
            "ocr_bin": str(local_ocr_bin),
            "sample_video": str(sample_video) if sample_video else None
        }

    # If models not found, download the archive
    zip_target = MODELS_DIR / "license-plate-reader.zip"
    if not zip_target.exists():
        ok = download_file(MODELS_ZIP_URL, zip_target, "Intel License Plate Reader model archive")
        if not ok:
            return {"status": "ERROR", "message": "Failed to download model zip archive"}

    # Extract zip
    print(f"[LPR Downloader] Extracting {zip_target}...")
    try:
        with zipfile.ZipFile(zip_target, "r") as z:
            z.extractall(MODELS_DIR)
    except Exception as e:
        return {"status": "ERROR", "message": f"Extraction error: {e}"}

    # Re-scan to locate extracted .xml and .bin files
    detected = find_existing_models()
    if not detected:
        return {"status": "ERROR", "message": "Extracted models could not be verified"}

    # Consolidate into top-level models directory
    final_det_xml = MODELS_DIR / "yolov8n_retrained.xml"
    final_det_bin = MODELS_DIR / "yolov8n_retrained.bin"
    final_ocr_xml = MODELS_DIR / "ch_PP-OCRv4_rec_infer.xml"
    final_ocr_bin = MODELS_DIR / "ch_PP-OCRv4_rec_infer.bin"

    if detected["detector_xml"] != final_det_xml:
        shutil.copy2(detected["detector_xml"], final_det_xml)
        shutil.copy2(detected["detector_bin"], final_det_bin)
    if detected["ocr_xml"] != final_ocr_xml:
        shutil.copy2(detected["ocr_xml"], final_ocr_xml)
        shutil.copy2(detected["ocr_bin"], final_ocr_bin)

    sample_video = ensure_sample_video()

    return {
        "status": "READY",
        "detector_xml": str(final_det_xml),
        "detector_bin": str(final_det_bin),
        "ocr_xml": str(final_ocr_xml),
        "ocr_bin": str(final_ocr_bin),
        "sample_video": str(sample_video) if sample_video else None
    }

def ensure_sample_video() -> Optional[Path]:
    """Ensure the sample ParkingVideo.mp4 is available."""
    video_path = SAMPLES_DIR / "ParkingVideo.mp4"
    if video_path.exists() and video_path.stat().st_size > 10000:
        return video_path

    # Check external repo
    ext_video = EXTERNAL_REPO_DIR / "ParkingVideo.mp4"
    if ext_video.exists() and ext_video.stat().st_size > 10000:
        shutil.copy2(ext_video, video_path)
        return video_path

    ok = download_file(SAMPLE_VIDEO_URL, video_path, "Intel sample video (ParkingVideo.mp4)")
    return video_path if ok else None

if __name__ == "__main__":
    res = ensure_models_available()
    print("Download result:", res)
