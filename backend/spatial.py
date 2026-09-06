"""
Geospatial math and spatial query utilities for CCTV GIS engine.
Includes Haversine distance, FOV cone coordinate calculation, and radius search.
"""
import math
from typing import List, Dict, Tuple, Any

def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance between two GPS coordinates in meters."""
    R = 6371000  # Radius of Earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_fov_cone_coordinates(
    lat: float, lon: float, azimuth_deg: float, fov_angle_deg: float, radius_meters: float
) -> List[Tuple[float, float]]:
    """
    Generate polygon boundary points (lat, lon) representing camera FOV cone.
    Azimuth: 0 = North, 90 = East, 180 = South, 270 = West.
    Returns list of (lat, lon) tuples forming a pie-wedge arc.
    """
    points = [(lat, lon)] # Apex of the cone
    start_angle = azimuth_deg - (fov_angle_deg / 2.0)
    end_angle = azimuth_deg + (fov_angle_deg / 2.0)
    
    # 10 intermediate points along arc for smooth curve
    steps = 10
    step_size = (end_angle - start_angle) / steps
    
    R = 6371000.0 # Earth radius
    for i in range(steps + 1):
        angle = math.radians(start_angle + i * step_size)
        # Bearing angle from North clockwise
        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)
        
        dest_lat = math.asin(
            math.sin(lat_rad) * math.cos(radius_meters / R) +
            math.cos(lat_rad) * math.sin(radius_meters / R) * math.cos(angle)
        )
        dest_lon = lon_rad + math.atan2(
            math.sin(angle) * math.sin(radius_meters / R) * math.cos(lat_rad),
            math.cos(radius_meters / R) - math.sin(lat_rad) * math.sin(dest_lat)
        )
        points.append((math.degrees(dest_lat), math.degrees(dest_lon)))
        
    points.append((lat, lon)) # Close polygon
    return points

def point_in_polygon(x: float, y: float, polygon: List[Dict[str, float]]) -> bool:
    """Ray-casting algorithm to test if point (x, y) is inside polygon."""
    n = len(polygon)
    inside = False
    p1x, p1y = polygon[0]['x'], polygon[0]['y']
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]['x'], polygon[i % n]['y']
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside
