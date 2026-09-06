"""
AI Engine, ANPR Route Reconstruction, Gap Analysis, and Bulk CSV Validation.
"""
import io
import csv
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple
from .models import Camera, AnprDetection, WatchlistItem, MaintenanceTicket, Department
from .spatial import haversine_distance_meters, calculate_fov_cone_coordinates

def reconstruct_vehicle_route(plate_number: str, detections: List[AnprDetection]) -> Dict[str, Any]:
    """
    Search ANPR detection logs for a plate number (case-insensitive substring match)
    and reconstruct chronological journey path across cameras.
    """
    clean_plate = plate_number.strip().upper()
    matching_dets = [
        d for d in detections if clean_plate in d.plate_number.upper()
    ]
    
    # Sort chronologically ascending for route reconstruction
    matching_dets.sort(key=lambda x: x.timestamp)
    
    waypoints = []
    total_dist_meters = 0.0

    for i, d in enumerate(matching_dets):
        waypoint = {
            "step": i + 1,
            "detection_id": d.id,
            "camera_id": d.camera_id,
            "camera_name": d.camera_name,
            "dept_name": d.dept_name,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "timestamp": d.timestamp,
            "plate_number": d.plate_number,
            "vehicle_type": d.vehicle_type,
            "vehicle_color": d.vehicle_color,
            "confidence": d.confidence,
            "snapshot_url": d.snapshot_url,
            "is_watchlist_hit": d.is_watchlist_hit,
            "watchlist_category": d.watchlist_category,
            "distance_from_prev_km": 0.0
        }

        if i > 0:
            prev = matching_dets[i - 1]
            dist = haversine_distance_meters(prev.latitude, prev.longitude, d.latitude, d.longitude)
            total_dist_meters += dist
            waypoint["distance_from_prev_km"] = round(dist / 1000.0, 2)

        waypoints.append(waypoint)

    return {
        "query_plate": clean_plate,
        "total_detections": len(waypoints),
        "total_distance_km": round(total_dist_meters / 1000.0, 2),
        "first_seen": waypoints[0]["timestamp"] if waypoints else None,
        "last_seen": waypoints[-1]["timestamp"] if waypoints else None,
        "waypoints": waypoints
    }

def analyze_infrastructure_gaps(cameras: List[Camera], departments: List[Department]) -> Dict[str, Any]:
    """
    Perform gap analysis:
    - Aging infrastructure (AMC expired or expiring in <= 60 days)
    - High offline ratio departments
    - Coverage density per district
    - Warranty expiration alerts
    """
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    sixty_days_str = (now + timedelta(days=60)).strftime("%Y-%m-%d")

    expired_amc = []
    expiring_soon_amc = []
    high_offline_depts = []
    district_counts: Dict[str, Dict[str, int]] = {}

    for cam in cameras:
        # District stats
        if cam.district not in district_counts:
            district_counts[cam.district] = {"total": 0, "online": 0, "offline": 0}
        district_counts[cam.district]["total"] += 1
        if cam.is_online:
            district_counts[cam.district]["online"] += 1
        else:
            district_counts[cam.district]["offline"] += 1

        # AMC checks
        if cam.amc_expiry < today_str:
            expired_amc.append({
                "camera_id": cam.id,
                "asset_code": cam.asset_code,
                "name": cam.name,
                "dept_name": cam.dept_name,
                "vendor_name": cam.vendor_name,
                "amc_expiry": cam.amc_expiry
            })
        elif cam.amc_expiry <= sixty_days_str:
            expiring_soon_amc.append({
                "camera_id": cam.id,
                "asset_code": cam.asset_code,
                "name": cam.name,
                "dept_name": cam.dept_name,
                "vendor_name": cam.vendor_name,
                "amc_expiry": cam.amc_expiry
            })

    # Department offline checks
    for dept in departments:
        dept_cams = [c for c in cameras if c.dept_id == dept.id]
        if dept_cams:
            offline_count = len([c for c in dept_cams if not c.is_online])
            offline_ratio = offline_count / len(dept_cams)
            if offline_ratio >= 0.20: # 20%+ offline
                high_offline_depts.append({
                    "dept_id": dept.id,
                    "dept_name": dept.name,
                    "total_cameras": len(dept_cams),
                    "offline_cameras": offline_count,
                    "offline_percentage": round(offline_ratio * 100, 1)
                })

    return {
        "expired_amc_count": len(expired_amc),
        "expiring_soon_amc_count": len(expiring_soon_amc),
        "expired_amc_list": expired_amc,
        "expiring_soon_amc_list": expiring_soon_amc,
        "high_offline_departments": high_offline_depts,
        "district_coverage_summary": district_counts
    }

def validate_bulk_csv_content(csv_raw_text: str) -> Dict[str, Any]:
    """
    Validate CSV for bulk camera onboarding.
    Enforces row-by-row schema validation, coordinate bounds check, duplicate IP/Asset check.
    Returns dry-run analysis with valid rows and error rows.
    """
    valid_rows = []
    error_rows = []
    seen_assets = set()
    seen_ips = set()

    try:
        reader = csv.DictReader(io.StringIO(csv_raw_text))
    except Exception as e:
        return {"success": False, "error": f"Invalid CSV File Format: {str(e)}"}

    required_headers = ["asset_code", "name", "dept_id", "camera_type", "latitude", "longitude"]
    if not reader.fieldnames or not all(h in reader.fieldnames for h in required_headers):
        return {
            "success": False,
            "error": f"Missing required headers. CSV must include: {', '.join(required_headers)}"
        }

    row_num = 1
    for row in reader:
        row_num += 1
        row_errors = []

        asset = row.get("asset_code", "").strip()
        name = row.get("name", "").strip()
        dept_id = row.get("dept_id", "").strip()
        cam_type = row.get("camera_type", "").strip()
        lat_str = row.get("latitude", "").strip()
        lng_str = row.get("longitude", "").strip()
        nvr_ip = row.get("nvr_ip", "").strip()

        # Validations
        if not asset:
            row_errors.append("Asset Code is required")
        elif asset in seen_assets:
            row_errors.append(f"Duplicate Asset Code '{asset}' within file")
        else:
            seen_assets.add(asset)

        if not name:
            row_errors.append("Camera Name is required")
        if not dept_id:
            row_errors.append("Department ID is required")

        # Coords
        try:
            lat = float(lat_str)
            if not (-90.0 <= lat <= 90.0):
                row_errors.append(f"Latitude {lat} out of bounds [-90, 90]")
        except ValueError:
            row_errors.append(f"Invalid latitude format: '{lat_str}'")

        try:
            lng = float(lng_str)
            if not (-180.0 <= lng <= 180.0):
                row_errors.append(f"Longitude {lng} out of bounds [-180, 180]")
        except ValueError:
            row_errors.append(f"Invalid longitude format: '{lng_str}'")

        if nvr_ip:
            if nvr_ip in seen_ips:
                row_errors.append(f"Duplicate NVR IP '{nvr_ip}'")
            else:
                seen_ips.add(nvr_ip)

        if row_errors:
            error_rows.append({
                "row_number": row_num,
                "asset_code": asset or "N/A",
                "name": name or "N/A",
                "errors": "; ".join(row_errors),
                "raw_data": row
            })
        else:
            valid_rows.append({
                "row_number": row_num,
                "asset_code": asset,
                "name": name,
                "dept_id": dept_id,
                "camera_type": cam_type or "IP Bullet",
                "latitude": float(lat_str),
                "longitude": float(lng_str),
                "nvr_ip": nvr_ip or f"10.0.{row_num}.1",
                "raw_data": row
            })

    return {
        "success": True,
        "total_rows_processed": row_num - 1,
        "valid_count": len(valid_rows),
        "error_count": len(error_rows),
        "valid_rows": valid_rows,
        "error_rows": error_rows
    }
