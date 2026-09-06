"""
Mock VMS Servers for Two-System Federation Demo Bench.
System A: Simulated Police Department VMS (Milestone XProtect REST schema, Port 8081)
System B: Simulated Municipal Corporation VMS (Hikvision ISAPI XML/JSON schema, Port 8082)
"""
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

POLICE_MILESTONE_DATA = {
    "system": "Milestone XProtect Corporate 2024 R1",
    "department": "Gujarat Police Department",
    "cameras": [
        {
            "CameraId": "MST-POL-001",
            "CameraName": "Highway Junction ANPR Pole #12",
            "Resolution": "3840x2160",
            "FPS": 30,
            "StreamUrl": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "Status": "Online",
            "Latitude": 23.0225,
            "Longitude": 72.5714
        },
        {
            "CameraId": "MST-POL-002",
            "CameraName": "Express Highway Toll Plaza",
            "Resolution": "1920x1080",
            "FPS": 60,
            "StreamUrl": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
            "Status": "Online",
            "Latitude": 23.0338,
            "Longitude": 72.5850
        }
    ],
    "events": [
        {
            "Id": "MST-EVT-9001",
            "Type": "ANPR_MATCH",
            "Plate": "GJ-01-AB-1234",
            "Confidence": 0.98,
            "CameraId": "MST-POL-002",
            "Timestamp": "2026-09-05 14:10:00"
        }
    ]
}

MUNICIPAL_HIKVISION_DATA = {
    "deviceInfo": {
        "deviceName": "Municipal Hikvision Central NVR Cluster",
        "firmwareVersion": "ISAPI v2.6.4",
        "department": "Food, Civil Supplies & Municipal Godowns"
    },
    "channels": [
        {
            "id": "HIK-CIV-101",
            "channelName": "Municipal Wholesale Market Gate #3",
            "videoCodec": "H.265",
            "streamUri": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
            "online": True,
            "latitude": 23.0180,
            "longitude": 72.5650
        },
        {
            "id": "HIK-CIV-102",
            "channelName": "Civic Center Godown Restricted Perimeter",
            "videoCodec": "H.264",
            "streamUri": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
            "online": True,
            "latitude": 23.0290,
            "longitude": 72.5790
        }
    ],
    "alertStreams": [
        {
            "alertId": "ISAPI-ALT-4002",
            "eventType": "PERIMETER_INTRUSION",
            "plateNumber": "GJ-01-AB-1234",
            "channelId": "HIK-CIV-102",
            "dateTime": "2026-09-05 14:14:00"
        }
    ]
}

class PoliceMilestoneHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(POLICE_MILESTONE_DATA).encode("utf-8"))

    def log_message(self, format, *args):
        return

class MunicipalHikvisionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(MUNICIPAL_HIKVISION_DATA).encode("utf-8"))

    def log_message(self, format, *args):
        return

def run_mock_servers():
    server_a = HTTPServer(("127.0.0.1", 8081), PoliceMilestoneHandler)
    server_b = HTTPServer(("127.0.0.1", 8082), MunicipalHikvisionHandler)

    t1 = threading.Thread(target=server_a.serve_forever, daemon=True)
    t2 = threading.Thread(target=server_b.serve_forever, daemon=True)
    t1.start()
    t2.start()

    print("System A (Police Milestone) running at http://127.0.0.1:8081")
    print("System B (Municipal Hikvision ISAPI) running at http://127.0.0.1:8082")
    return server_a, server_b

if __name__ == "__main__":
    s_a, s_b = run_mock_servers()
    print("Press Ctrl+C to stop mock VMS servers.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("Stopping mock servers.")
