"""
Pluggable VMS Adapter & Connector Framework.
Provides standard abstraction across Milestone, Hikvision ISAPI, Dahua, Axis, and Generic ONVIF.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from backend.models import VMSPlatform

class BaseVMSAdapter(ABC):
    """
    Abstract VMS Adapter interface defining protocol contract.
    """
    def __init__(self, platform: VMSPlatform):
        self.platform = platform
        self.cached_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

    @abstractmethod
    def authenticate(self) -> Dict[str, Any]:
        """Authenticate against external VMS and return session token/credentials."""
        pass

    @abstractmethod
    def fetch_camera_list(self) -> List[Dict[str, Any]]:
        """Query VMS registry to fetch all cameras and channel feeds."""
        pass

    @abstractmethod
    def get_stream_handle(self, camera_id: str) -> Dict[str, Any]:
        """Resolve live streaming handle (RTSP, HLS, WebRTC) for camera."""
        pass

    @abstractmethod
    def subscribe_events(self) -> List[Dict[str, Any]]:
        """Fetch or receive real-time event telemetry (ANPR, motion, perimeter)."""
        pass

    @abstractmethod
    def poll_telemetry(self) -> Dict[str, Any]:
        """Query VMS health, storage, and node heartbeat telemetry."""
        pass


class MilestoneAdapter(BaseVMSAdapter):
    """
    Milestone XProtect REST / SOAP Protocol Adapter.
    Simulates token-based authentication, camera discovery, and MIP SDK event integration.
    """
    def authenticate(self) -> Dict[str, Any]:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        self.cached_token = f"mst_token_{self.platform.id[:8]}_{now_ts}"
        return {
            "success": True,
            "vendor": "Milestone Systems",
            "token_type": "Bearer",
            "access_token": self.cached_token,
            "expires_in": 3600,
            "api_version": "2024.1-REST"
        }

    def fetch_camera_list(self) -> List[Dict[str, Any]]:
        # Deterministic camera feeds based on platform id
        return [
            {
                "id": f"{self.platform.id}-CAM-001",
                "vms_camera_id": f"{self.platform.id}-CAM-001",
                "name": f"{self.platform.name} - Traffic Junction High-Res",
                "resolution": "3840x2160 (4K)",
                "fps": 30,
                "bitrate_kbps": 6144,
                "protocol": "RTSP-Over-HTTP",
                "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "is_online": True,
                "latitude": 23.0225,
                "longitude": 72.5714,
                "camera_type": "PTZ Dome",
                "vendor_device": "Axis Q6135-LE via Milestone"
            },
            {
                "id": f"{self.platform.id}-CAM-002",
                "vms_camera_id": f"{self.platform.id}-CAM-002",
                "name": f"{self.platform.name} - Express Highway ANPR Toll",
                "resolution": "1920x1080",
                "fps": 60,
                "bitrate_kbps": 4096,
                "protocol": "HLS",
                "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "is_online": True,
                "latitude": 23.0338,
                "longitude": 72.5850,
                "camera_type": "Fixed Bullet ANPR",
                "vendor_device": "Milestone Husky IVO"
            }
        ]

    def get_stream_handle(self, camera_id: str) -> Dict[str, Any]:
        if not self.cached_token:
            self.authenticate()
        return {
            "camera_id": camera_id,
            "protocol": "HLS",
            "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "token_auth": self.cached_token,
            "vendor": "Milestone XProtect",
            "mime_type": "application/x-mpegURL",
            "latency_ms": 120
        }

    def subscribe_events(self) -> List[Dict[str, Any]]:
        # Set 5 minutes prior to demonstrate cross-system correlation within 15-min window
        evt_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        return [
            {
                "event_id": f"EVT-MST-{int(datetime.now(timezone.utc).timestamp())}-01",
                "vms_platform_id": self.platform.id,
                "vms_name": self.platform.name,
                "vendor": self.platform.vendor,
                "department_id": self.platform.department_id,
                "department_name": "Gujarat Police Department",
                "event_type": "ANPR_MATCH",
                "topic": "cctv.events.detections",
                "severity": "HIGH",
                "timestamp": evt_time,
                "camera_id": f"{self.platform.id}-CAM-002",
                "camera_name": f"{self.platform.name} - Express Highway ANPR Toll",
                "plate_number": "GJ-01-AB-1234",
                "confidence": 0.96,
                "payload": {"speed_kmph": 78, "lane": 2, "watchlist_flag": True}
            }
        ]

    def poll_telemetry(self) -> Dict[str, Any]:
        return {
            "vms_id": self.platform.id,
            "vendor": "Milestone",
            "status": "ONLINE",
            "cpu_usage_pct": 28.4,
            "ram_usage_gb": 12.8,
            "recording_storage_tb_used": 142.5,
            "active_client_streams": 14,
            "recording_servers_online": 3,
            "last_heartbeat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }


class HikvisionISAPIAdapter(BaseVMSAdapter):
    """
    Hikvision ISAPI Protocol Adapter.
    Simulates XML/REST ISAPI endpoints for channel status, alert streams, and RTSP stream mappings.
    """
    def authenticate(self) -> Dict[str, Any]:
        self.cached_token = f"isapi_digest_session_{self.platform.id[:8]}"
        return {
            "success": True,
            "vendor": "Hikvision",
            "auth_type": "ISAPI-Digest",
            "session_id": self.cached_token,
            "isapi_version": "v2.6"
        }

    def fetch_camera_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": f"{self.platform.id}-CH-101",
                "vms_camera_id": f"{self.platform.id}-CH-101",
                "name": f"{self.platform.name} - Municipal Market Gate North",
                "resolution": "2560x1440 (2K)",
                "fps": 25,
                "bitrate_kbps": 4096,
                "protocol": "RTSP",
                "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "is_online": True,
                "latitude": 23.0180,
                "longitude": 72.5650,
                "camera_type": "DarkFighter Bullet",
                "vendor_device": "Hikvision DS-2CD2047G2"
            },
            {
                "id": f"{self.platform.id}-CH-102",
                "vms_camera_id": f"{self.platform.id}-CH-102",
                "name": f"{self.platform.name} - Civic Center Perimeter Intrusions",
                "resolution": "1920x1080",
                "fps": 30,
                "bitrate_kbps": 2048,
                "protocol": "HLS",
                "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
                "is_online": True,
                "latitude": 23.0290,
                "longitude": 72.5790,
                "camera_type": "Thermal Bi-Spectrum",
                "vendor_device": "Hikvision DS-2TD2137"
            }
        ]

    def get_stream_handle(self, camera_id: str) -> Dict[str, Any]:
        return {
            "camera_id": camera_id,
            "protocol": "RTSP",
            "stream_url": f"rtsp://hikvision-isapi.civic.local:554/Streaming/Channels/101",
            "fallback_hls": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
            "vendor": "Hikvision ISAPI",
            "isapi_channel": "101",
            "rtsp_transport": "TCP"
        }

    def subscribe_events(self) -> List[Dict[str, Any]]:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        return [
            {
                "event_id": f"EVT-HIK-{int(datetime.now(timezone.utc).timestamp())}-02",
                "vms_platform_id": self.platform.id,
                "vms_name": self.platform.name,
                "vendor": self.platform.vendor,
                "department_id": self.platform.department_id,
                "department_name": "Municipal Corporation",
                "event_type": "PERIMETER_INTRUSION",
                "topic": "cctv.events.alerts",
                "severity": "CRITICAL",
                "timestamp": now_str,
                "camera_id": f"{self.platform.id}-CH-102",
                "camera_name": f"{self.platform.name} - Civic Center Perimeter Intrusions",
                "plate_number": "GJ-01-AB-1234", # Correlatable plate!
                "confidence": 0.94,
                "payload": {"intrusion_polygon": "Zone-A-North", "target_type": "Vehicle"}
            }
        ]

    def poll_telemetry(self) -> Dict[str, Any]:
        return {
            "vms_id": self.platform.id,
            "vendor": "Hikvision",
            "status": "ONLINE",
            "isapi_channels_active": 32,
            "nvr_storage_health": "OK",
            "network_in_mbps": 118.2,
            "last_heartbeat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }


class GenericONVIFAdapter(BaseVMSAdapter):
    """
    Generic ONVIF Profile S/T Adapter fallback.
    """
    def authenticate(self) -> Dict[str, Any]:
        return {"success": True, "vendor": "Generic ONVIF", "token_type": "WS-Security"}

    def fetch_camera_list(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": f"{self.platform.id}-ONVIF-01",
                "vms_camera_id": f"{self.platform.id}-ONVIF-01",
                "name": f"{self.platform.name} - Standard Profile S Node",
                "resolution": "1920x1080",
                "fps": 25,
                "bitrate_kbps": 2048,
                "protocol": "ONVIF/RTSP",
                "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "is_online": True,
                "latitude": 23.0200,
                "longitude": 72.5700,
                "camera_type": "Fixed Dome",
                "vendor_device": "Generic ONVIF Conformant"
            }
        ]

    def get_stream_handle(self, camera_id: str) -> Dict[str, Any]:
        return {
            "camera_id": camera_id,
            "protocol": "RTSP",
            "stream_url": "rtsp://onvif.generic.local:554/media/profile1",
            "vendor": "ONVIF Profile S"
        }

    def subscribe_events(self) -> List[Dict[str, Any]]:
        return []

    def poll_telemetry(self) -> Dict[str, Any]:
        return {
            "vms_id": self.platform.id,
            "vendor": "Generic ONVIF",
            "status": "ONLINE",
            "last_heartbeat": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }


class VMSAdapterFactory:
    """
    Dynamic factory resolving appropriate adapter based on VMS vendor or adapter type.
    """
    @staticmethod
    def get_adapter(platform: VMSPlatform) -> BaseVMSAdapter:
        adapter_type = (platform.adapter_type or "").lower()
        vendor = (platform.vendor or "").lower()

        if "milestone" in adapter_type or "milestone" in vendor:
            return MilestoneAdapter(platform)
        elif "hikvision" in adapter_type or "isapi" in adapter_type or "hikvision" in vendor:
            return HikvisionISAPIAdapter(platform)
        else:
            return GenericONVIFAdapter(platform)
