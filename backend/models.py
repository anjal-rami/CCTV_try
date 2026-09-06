"""
Data models and schemas for Enterprise CCTV Registry, Federation & Analytics Platform.
Includes 8 Authority Roles (RBAC), JWT schemas, Security Incident tracking, and TOTP MFA.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from enum import Enum

class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"
    DEPARTMENT_ADMIN = "DEPARTMENT_ADMIN"
    AI_ANALYST = "AI_ANALYST"
    GIS_OPERATOR = "GIS_OPERATOR"
    MAINTENANCE_OFFICER = "MAINTENANCE_OFFICER"
    TECHNICIAN = "TECHNICIAN"
    OPERATOR = "OPERATOR"

class CameraStatus(str, Enum):
    PLANNED = "Planned"
    PROCURED = "Procured"
    INSTALLED = "Installed"
    ACTIVE = "Active"
    MAINTENANCE_DUE = "Maintenance Due"
    FAULT_REPAIR = "Fault/Repair"
    REPLACEMENT = "Replacement"
    DECOMMISSIONED = "Decommissioned"

class TicketSeverity(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

class TicketStatus(str, Enum):
    OPEN = "Open"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    AWAITING_PARTS = "Awaiting Parts"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

@dataclass
class User:
    id: str
    name: str
    email: str
    password_hash: str
    role: UserRole
    role_title: str
    username: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    badge_code: str = "GJ-000"
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    is_active: bool = True
    status: str = "ACTIVE" # ACTIVE, PENDING_APPROVAL, APPROVED, REJECTED
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    created_at: str = "2026-09-05 10:00:00"

    @property
    def verification_status(self) -> str:
        if self.status in ["ACTIVE", "APPROVED"] and self.is_active:
            return "APPROVED"
        return self.status

    @verification_status.setter
    def verification_status(self, val: str):
        self.status = val

    @property
    def full_name(self) -> str:
        return self.name

    @full_name.setter
    def full_name(self, val: str):
        self.name = val

    @property
    def department(self) -> str:
        return self.department_name or ""

    @department.setter
    def department(self, val: str):
        self.department_name = val

    @property
    def employee_id(self) -> str:
        return self.badge_code

    @employee_id.setter
    def employee_id(self, val: str):
        self.badge_code = val

@dataclass
class Department:
    id: str
    name: str
    code: str
    category: str
    nodal_officer: str
    contact_email: str
    active_cameras: int = 0
    total_cameras: int = 0

@dataclass
class Camera:
    id: str
    asset_code: str
    name: str
    dept_id: str
    dept_name: str
    station_division: str
    responsible_officer: str
    officer_phone: str
    
    # Geospatial
    state: str
    district: str
    taluka: str
    ward_zone: str
    latitude: float
    longitude: float
    altitude: float
    fov_azimuth: float
    fov_angle: float
    coverage_radius: float
    
    # Technical
    camera_type: str
    resolution: str
    fps: int
    bitrate_kbps: int
    
    # Storage
    storage_arch: str
    nvr_ip: str
    nvr_port: int
    storage_tb: float
    retention_days: int
    
    # Network & Streaming
    link_type: str
    bandwidth_mbps: int
    protocol: str
    stream_url: str
    
    # Ownership & Vendor
    ownership: str
    vendor_name: str
    amc_expiry: str
    warranty_status: str
    
    # Status & Health
    status: str
    is_online: bool
    last_ping: str
    health_score: int
    vms_platform_id: Optional[str] = None

@dataclass
class AuditLog:
    id: str
    camera_id: Optional[str]
    timestamp: str
    user_id: str
    user_name: str
    role: str
    action_type: str        # READ_QUERY, STATE_TRANSITION, ANPR_SEARCH, SECURITY_ALERT, LOGIN_ATTEMPT
    previous_state: Optional[str]
    new_state: Optional[str]
    justification: str
    client_ip: str = "127.0.0.1"

# Ponytail Rule 6: Immutable Security Audit Log Standard
SecurityAuditLog = AuditLog


@dataclass
class SecurityThreatIncident:
    id: str
    incident_code: str
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW
    threat_type: str       # Failed Login Spike, Rate Limit Breach, Unauthorized Route Access, IP Attack Pattern
    source_ip: str
    user_email: Optional[str]
    timestamp: str
    status: str            # ACTIVE, BLOCKED, INVESTIGATING, RESOLVED
    details: str

@dataclass
class BlockedIpRecord:
    ip_address: str
    reason: str
    blocked_at: str
    blocked_by: str

@dataclass
class AnprDetection:
    id: str
    camera_id: str
    camera_name: str
    dept_name: str
    latitude: float
    longitude: float
    plate_number: str
    vehicle_type: str
    vehicle_color: str
    confidence: float
    timestamp: str
    snapshot_url: str
    is_watchlist_hit: bool
    watchlist_category: Optional[str] = None

@dataclass
class WatchlistItem:
    id: str
    plate_number: str
    category: str
    description: str
    flagged_by: str
    created_at: str
    severity: str

@dataclass
class MaintenanceTicket:
    id: str
    ticket_code: str
    camera_id: str
    camera_name: str
    dept_id: str
    dept_name: str
    issue_type: str
    severity: str
    status: str
    created_at: str
    sla_due_at: str
    assigned_technician_id: str
    assigned_technician_name: str
    vendor_name: str
    repair_cost_inr: float
    resolution_summary: Optional[str] = None
    photo_evidence_url: Optional[str] = None

@dataclass
class VMSPlatform:
    id: str
    name: str
    department_id: str
    vendor: str                         # Milestone, Hikvision, Dahua, Honeywell, Axis, Uniview
    version: str                        # e.g., "XProtect 2024 R1", "ISAPI v2.6"
    protocol: str                       # ONVIF, RTSP, REST API, Vendor SDK
    base_endpoint_url: str
    credential_secret_ref: str
    adapter_type: str                   # milestone, hikvision_isapi, generic_onvif
    status: str                         # ONLINE, OFFLINE, DEGRADED
    created_at: str
    last_sync_at: Optional[str] = None
    synced_cameras_count: int = 0

@dataclass
class FederatedEvent:
    id: str
    vms_platform_id: str
    vms_name: str
    vendor: str
    camera_id: str
    camera_name: str
    department_id: str
    department_name: str
    topic: str                          # cctv.events.detections, cctv.events.camera_status, cctv.events.alerts
    event_type: str                     # ANPR_MATCH, PERIMETER_INTRUSION, OBJECT_DETECTED, STREAM_OFFLINE, HIGHWAY_SPEED
    severity: str                       # CRITICAL, HIGH, MEDIUM, LOW, INFO
    timestamp: str
    plate_number: Optional[str] = None
    confidence: float = 0.95
    payload: Optional[Dict[str, Any]] = None
    raw_signature: Optional[str] = None

@dataclass
class CorrelatedIncident:
    id: str
    title: str
    correlation_type: str               # SPATIAL_TEMPORAL, CROSS_DEPARTMENT_ESCALATION, MULTI_VMS_PLATE_HIT
    source_vms_ids: List[str]
    departments_involved: List[str]
    plate_number: Optional[str]
    confidence: float
    severity: str                       # CRITICAL, HIGH, MEDIUM
    first_detected_at: str
    last_detected_at: str
    time_window_minutes: float
    event_count: int
    details: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    workflow_task_id: Optional[str] = None
    status: str = "OPEN"                # OPEN, ESCALATED, RESOLVED

@dataclass
class WorkflowTask:
    id: str
    title: str
    event_id: Optional[str]
    correlation_id: Optional[str]
    source_department: str
    assigned_department: str
    priority: str                       # CRITICAL, HIGH, MEDIUM, LOW
    status: str                         # OPEN, IN_PROGRESS, ESCALATED, RESOLVED
    sop_checklist: List[Dict[str, Any]] # [{"id": 1, "task": "...", "completed": False, "verified_by": None}]
    escalation_deadline: str
    created_at: str
    notes: Optional[str] = None
    resolution_summary: Optional[str] = None
    resolved_by: Optional[str] = None

