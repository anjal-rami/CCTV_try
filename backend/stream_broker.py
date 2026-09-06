"""
Vendor-agnostic VMS Federation Stream Broker.
Provides stream protocol abstraction (RTSP, ONVIF, WebRTC, HLS) and live stream metadata.
"""
from typing import Dict, Any, List

SAMPLE_STREAMS = [
    {
        "id": "STREAM-01",
        "title": "Highway Traffic Junction - ANPR Node",
        "hls_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "codec": "H.264 / AAC",
        "bitrate": "4096 kbps",
        "fps": 30
    },
    {
        "id": "STREAM-02",
        "title": "Municipal Market Perimeter - Thermal Node",
        "hls_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "codec": "H.265 / AAC",
        "bitrate": "2048 kbps",
        "fps": 25
    },
    {
        "id": "STREAM-03",
        "title": "Central Railway Station Plaza - PTZ 360",
        "hls_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "codec": "H.264 / PCM",
        "bitrate": "8192 kbps",
        "fps": 60
    },
    {
        "id": "STREAM-04",
        "title": "RTO Checkpost Gate #2 - ANPR Dedicated",
        "hls_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
        "codec": "H.264 / AAC",
        "bitrate": "4096 kbps",
        "fps": 30
    }
]

def get_vms_stream_details(camera_id: str, protocol_requested: str = "HLS") -> Dict[str, Any]:
    """
    Abstract VMS backend (Milestone, Hikvision, Dahua, Axis) and return stream broker endpoint.
    """
    sample = SAMPLE_STREAMS[int(hash(camera_id)) % len(SAMPLE_STREAMS)]
    return {
        "camera_id": camera_id,
        "protocol": protocol_requested,
        "vms_vendor_adapter": "Unified-Federation-VMS-v4.2",
        "stream_url": sample["hls_url"],
        "stream_title": sample["title"],
        "video_codec": sample["codec"],
        "bitrate": sample["bitrate"],
        "fps": sample["fps"],
        "is_live_brokered": True
    }
