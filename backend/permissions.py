"""
Ironclad Zero-Trust Access Boundary Enforcement Engine.
Provides granular permission dependencies, role-to-permission mappings,
Row-Level Security (RLS) department scoping, and field-level immutability guards.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from fastapi import Depends, HTTPException, status, Header
from datetime import datetime, timezone

from .models import UserRole, SecurityThreatIncident, AuditLog

class Permission(str, Enum):
    CAMERA_CREATE = "camera:create"
    CAMERA_UPDATE_FULL = "camera:update_full"
    CAMERA_UPDATE_SPATIAL = "camera:update_spatial"
    CAMERA_DELETE = "camera:delete"
    CAMERA_TRANSITION_LIFECYCLE = "camera:transition_lifecycle"
    CAMERA_READ_METADATA = "camera:read_metadata"
    CAMERA_READ_CREDENTIALS = "camera:read_credentials"
    CAMERA_BULK_IMPORT = "camera:bulk_import"
    WATCHLIST_MUTATE = "watchlist:mutate"
    TRACKING_ACCESS = "tracking:access"
    AUDIT_READ = "audit:read"
    TELEMETRY_WRITE = "telemetry:write"

# Exhaustive Role Permissions Registry across all 8 Authorities
ROLE_PERMISSIONS_REGISTRY: Dict[str, List[Permission]] = {
    UserRole.SUPER_ADMIN.value: list(Permission),
    UserRole.SECURITY_ADMIN.value: [
        Permission.AUDIT_READ,
        Permission.CAMERA_READ_METADATA,
    ],
    UserRole.DEPARTMENT_ADMIN.value: [
        Permission.CAMERA_CREATE,
        Permission.CAMERA_UPDATE_FULL,
        Permission.CAMERA_UPDATE_SPATIAL,
        Permission.CAMERA_DELETE,
        Permission.CAMERA_TRANSITION_LIFECYCLE,
        Permission.CAMERA_READ_METADATA,
        Permission.CAMERA_READ_CREDENTIALS,
        Permission.CAMERA_BULK_IMPORT,
    ],
    UserRole.GIS_OPERATOR.value: [
        Permission.CAMERA_UPDATE_SPATIAL,
        Permission.CAMERA_READ_METADATA,
    ],
    UserRole.MAINTENANCE_OFFICER.value: [
        Permission.CAMERA_TRANSITION_LIFECYCLE,
        Permission.CAMERA_READ_METADATA,
    ],
    UserRole.AI_ANALYST.value: [
        Permission.CAMERA_READ_METADATA,
        Permission.CAMERA_READ_CREDENTIALS,
        Permission.WATCHLIST_MUTATE,
        Permission.TRACKING_ACCESS,
    ],
    UserRole.TECHNICIAN.value: [
        Permission.CAMERA_READ_METADATA,
    ],
    UserRole.OPERATOR.value: [
        Permission.CAMERA_READ_METADATA,
    ],
    "AUDITOR": [
        Permission.CAMERA_READ_METADATA,
        Permission.AUDIT_READ,
    ]
}

# Automated health metrics that are IMMUTABLE to human users
AUTOMATED_HEALTH_METRICS: Set[str] = {
    "health_status",
    "is_online",
    "last_ping",
    "last_heartbeat",
    "downtime_duration",
    "packet_loss_pct",
    "health_score"
}

# Fields allowed for spatial updates by GIS_OPERATOR
SPATIAL_ALLOWED_FIELDS: Set[str] = {
    "latitude",
    "longitude",
    "altitude",
    "fov_azimuth",
    "fov_angle",
    "coverage_radius",
    "ward_zone",
    "taluka",
    "district",
    "state"
}

def require_permission(required_perm: Permission):
    """
    FastAPI permission dependency.
    Evaluates current user's role against the ROLE_PERMISSIONS_REGISTRY.
    """
    from .main import get_current_user, SECURITY_INCIDENTS
    
    def permission_checker(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required."
            )
            
        user_role = current_user.get("role")
        user_perms = ROLE_PERMISSIONS_REGISTRY.get(user_role, [])
        
        if required_perm not in user_perms and user_role != UserRole.SUPER_ADMIN.value:
            # Log security incident
            SECURITY_INCIDENTS.append(SecurityThreatIncident(
                id=f"INC-SEC-{len(SECURITY_INCIDENTS)+1:03d}",
                incident_code=f"SEC-2024-{len(SECURITY_INCIDENTS)+1:04d}",
                severity="HIGH",
                threat_type="UNAUTHORIZED_PERMISSION_ATTEMPT",
                source_ip="127.0.0.1",
                user_email=current_user.get("email", "unknown@platform.gov.in"),
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                status="ACTIVE",
                details=f"User {current_user.get('name')} ({user_role}) attempted operation requiring '{required_perm.value}' outside role authority boundary."
            ))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "INSUFFICIENT_PERMISSIONS",
                    "required_permission": required_perm.value,
                    "role": user_role,
                    "message": "Action strictly outside user authority boundary."
                }
            )
        return current_user

    return permission_checker

def check_department_scope(user: Dict[str, Any], target_dept_id: str):
    """
    Enforces Row-Level Security (RLS) department boundaries.
    Department-scoped roles (e.g. DEPARTMENT_ADMIN) are strictly limited to their assigned department.
    Statewide roles (SUPER_ADMIN, GIS_OPERATOR, MAINTENANCE_OFFICER, etc.) with department_id=None can operate across departments within their permission matrix.
    """
    from .main import SECURITY_INCIDENTS
    
    user_role = user.get("role")
    user_dept = user.get("department_id")

    if user_role == UserRole.SUPER_ADMIN.value or user_dept is None:
        return
        
    if user_dept != target_dept_id:
        SECURITY_INCIDENTS.append(SecurityThreatIncident(
            id=f"INC-SEC-{len(SECURITY_INCIDENTS)+1:03d}",
            incident_code=f"SEC-2024-{len(SECURITY_INCIDENTS)+1:04d}",
            severity="HIGH",
            threat_type="CROSS_DEPARTMENT_ACCESS_VIOLATION",
            source_ip="127.0.0.1",
            user_email=user.get("email", "unknown@platform.gov.in"),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            status="ACTIVE",
            details=f"RLS Violation: User {user.get('name')} ({user_role}, Dept: {user_dept}) attempted unauthorized access to target department '{target_dept_id}'."
        ))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Forbidden: Operational jurisdiction restricted to department '{user_dept}'."
        )

def check_field_mutation_boundary(user: Dict[str, Any], update_payload: Dict[str, Any], is_spatial_only: bool = False):
    """
    Enforces field-level immutability and zero-trust domain boundaries:
    1. Blocks manual human modification of automated telemetry health fields.
    2. Enforces strict spatial-only field limits for GIS operators.
    """
    user_role = user.get("role")
    payload_keys = set(update_payload.keys())
    
    # 1. System Health Metrics are Automated & Immutable to all human users
    attempted_health_mutations = payload_keys.intersection(AUTOMATED_HEALTH_METRICS)
    if attempted_health_mutations:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Forbidden: System health metrics {list(attempted_health_mutations)} are immutable and updated exclusively via automated internal telemetry ingestion."
        )
        
    # 2. GIS_OPERATOR Field-Level Restrictions
    if user_role == UserRole.GIS_OPERATOR.value or is_spatial_only:
        disallowed_fields = payload_keys - SPATIAL_ALLOWED_FIELDS
        if disallowed_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Forbidden: Spatial update endpoint strictly prohibits editing non-spatial fields: {list(disallowed_fields)}."
            )
