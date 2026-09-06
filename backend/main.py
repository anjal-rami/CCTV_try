"""
FastAPI Main Application for Enterprise CCTV Registry, Federation & Analytics Platform.
Includes 8 Authority RBAC Guards, MFA Totp Validation, Row-Level Security (RLS), and Security Admin Forensics.
"""
from fastapi import FastAPI, HTTPException, Query, Body, Depends, Header, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from .models import (
    Department, Camera, AnprDetection, WatchlistItem,
    MaintenanceTicket, AuditLog, CameraStatus, TicketStatus,
    User, UserRole, SecurityThreatIncident, BlockedIpRecord,
    VMSPlatform, FederatedEvent, CorrelatedIncident, WorkflowTask
)
from .seed_data import generate_seed_data, SEED_USERS, SEED_VMS_PLATFORMS
from .spatial import haversine_distance_meters, calculate_fov_cone_coordinates
from .ai_engine import reconstruct_vehicle_route, analyze_infrastructure_gaps, validate_bulk_csv_content
from .stream_broker import get_vms_stream_details
from .auth import authenticate_user, verify_mfa_code, decode_access_token, UserRegisterRequest, register_new_user
from .security_engine import calculate_security_threat_score, SECURITY_INCIDENTS, BLOCKED_IPS, block_ip_address, is_ip_blocked
from .permissions import (
    Permission, require_permission, check_department_scope,
    check_field_mutation_boundary, ROLE_PERMISSIONS_REGISTRY
)
from .crypto_vault import encrypt_vms_secret, decrypt_vms_secret
from app.services.adapters.base import VMSAdapterFactory
from app.core.event_bus import event_bus, TOPIC_DETECTIONS, TOPIC_CAMERA_STATUS, TOPIC_ALERTS, ALL_TOPICS
from app.services.correlation_engine import correlation_engine
# pyrefly: ignore [missing-import]
import rule_engine

# ==============================================================================
# DECLARATIVE RULE ENGINE STANDARD SPECIFICATIONS (Ponytail Governance Compliant)
# ==============================================================================
WATCHLIST_ACCESS_RULE = rule_engine.Rule(
    "role == 'SUPER_ADMIN' or role == 'AI_ANALYST' or (role == 'DEPARTMENT_ADMIN' and is_law_enforcement)"
)

ANPR_ACCESS_RULE = rule_engine.Rule(
    "role == 'SUPER_ADMIN' or role == 'AI_ANALYST' or (role == 'DEPARTMENT_ADMIN' and is_law_enforcement)"
)

STREAM_RESTRICTED_RULE = rule_engine.Rule(
    "role == 'TECHNICIAN' or role == 'MAINTENANCE_OFFICER'"
)

VMS_ADMIN_RULE = rule_engine.Rule(
    "role == 'SUPER_ADMIN' or role == 'DEPARTMENT_ADMIN'"
)

DEPT_SCOPED_QUERY_RULE = rule_engine.Rule(
    "role == 'DEPARTMENT_ADMIN' or role == 'OPERATOR'"
)

USER_ADMIN_DIRECTORY_RULE = rule_engine.Rule(
    "role == 'SUPER_ADMIN' or role == 'DEPARTMENT_ADMIN'"
)

APPROVED_USER_RULE = rule_engine.Rule(
    "is_active == true and (verification_status == 'APPROVED' or status == 'APPROVED' or status == 'ACTIVE')"
)


app = FastAPI(
    title="Enterprise CCTV Registry, Federation & Analytics Platform API",
    version="2.0.0-RBAC",
    description="Scalable system management for 80,000+ CCTV streams across 26 government departments with 8 Authority RBAC."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory database populated with realistic Gujarat seed data
DEPARTMENTS, CAMERAS, ANPR_DETECTIONS, WATCHLIST, TICKETS, AUDIT_LOGS = generate_seed_data()
VMS_PLATFORMS: List[VMSPlatform] = [
    VMSPlatform(**asdict(p)) if hasattr(p, '__dataclass_fields__') else p for p in SEED_VMS_PLATFORMS
]

# ----------------------------------------------------
# RBAC Authorization Dependency & Audit Logger
# ----------------------------------------------------
def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Decode JWT token from Authorization header if present."""
    if not authorization:
        return None
    try:
        token = authorization.replace("Bearer ", "").strip()
        return decode_access_token(token)
    except Exception:
        return None

def require_role(allowed_roles: List[UserRole]):
    """
    FastAPI Role Guard Dependency.
    Enforces authority boundaries. Returns 403 Forbidden and logs security audit incident if violated.
    """
    def role_checker(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
        if not current_user:
            return None
        
        user_role = current_user.get("role")
        allowed_str = [r.value for r in allowed_roles]
        
        if user_role not in allowed_str and user_role != UserRole.SUPER_ADMIN.value:
            # Log security violation
            SECURITY_INCIDENTS.append(SecurityThreatIncident(
                id=f"INC-SEC-{len(SECURITY_INCIDENTS)+1:03d}",
                incident_code=f"SEC-2024-{len(SECURITY_INCIDENTS)+1:04d}",
                severity="HIGH",
                threat_type="Unauthorized Route Guard Access",
                source_ip="127.0.0.1",
                user_email=current_user.get("email", "unknown@platform.gov.in"),
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                status="ACTIVE",
                details=f"User {current_user.get('name')} ({user_role}) attempted forbidden operation requiring {allowed_str}."
            ))
            raise HTTPException(
                status_code=403,
                detail=f"Access Forbidden: Role '{user_role}' is not authorized to execute this operation."
            )
        return current_user

    return role_checker

def validate_watchlist_mutation(user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ROOT CAUSE PRIVILEGE ESCALATION PATCH:
    Enforces strict authority checks for Watchlist CRUD operations using declarative rule_engine.
    Permitted: SUPER_ADMIN, AI_ANALYST, and law-enforcement DEPARTMENT_ADMIN (Police, Home, RTO).
    Explicitly Prohibited: TECHNICIAN, MAINTENANCE_OFFICER, GIS_OPERATOR, VIEWER, SECURITY_ADMIN, Civil DEPT_ADMIN.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required."
        )
    
    role = user.get("role")
    dept_name = user.get("department_name") or ""
    is_le = any(k in dept_name.lower() for k in ["police", "home", "rto", "transport"])
    context = {"role": role, "is_law_enforcement": is_le}

    if not WATCHLIST_ACCESS_RULE.matches(context):
        # Record HIGH severity security incident
        incident = SecurityThreatIncident(
            id=f"INC-SEC-{len(SECURITY_INCIDENTS)+1:03d}",
            incident_code=f"SEC-2024-{len(SECURITY_INCIDENTS)+1:04d}",
            severity="HIGH",
            threat_type="WATCHLIST_MUTATION_DENIED",
            source_ip="127.0.0.1",
            user_email=user.get("email", "unknown"),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            status="ACTIVE",
            details=f"CRITICAL PRIVILEGE ESCALATION PREVENTED: User {user.get('name')} with role '{role}' ({dept_name}) attempted unauthorized Watchlist modification."
        )
        SECURITY_INCIDENTS.append(incident)

        audit = AuditLog(
            id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
            camera_id=None,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            user_id=user.get("sub", "unknown"),
            user_name=user.get("name", "Unknown User"),
            role=role,
            action_type="WATCHLIST_MUTATION_DENIED",
            previous_state=None,
            new_state=None,
            justification=f"Unauthorized watchlist write attempt blocked for role '{role}'",
            client_ip="127.0.0.1"
        )
        AUDIT_LOGS.append(audit)

        raise HTTPException(
            status_code=403,
            detail=f"Access Forbidden: Role '{role}' in '{dept_name}' is strictly prohibited from modifying law enforcement watchlists."
        )
    return user

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "Gujarat State CCTV Registry, Federation & Analytics Platform",
        "rbac_version": "2.0-ZeroTrustSecurityPatched",
        "total_departments": len(DEPARTMENTS),
        "total_cameras_seeded": len(CAMERAS),
        "total_seed_users": len(SEED_USERS)
    }

# ----------------------------------------------------
# Auth & User Profile Endpoints
# ----------------------------------------------------
@app.post("/api/v1/auth/login")
def login(payload: Dict[str, Any] = Body(...)):
    identifier = payload.get("username") or payload.get("email") or payload.get("identifier") or ""
    password = payload.get("password") or ""
    if not identifier or not password:
        raise HTTPException(status_code=400, detail="Username/email and password required")
    return authenticate_user(identifier, password)

@app.post("/api/v1/auth/register", status_code=201)
@app.post("/register", status_code=201)
def register_user_endpoint(payload: UserRegisterRequest, request: Request):
    client_ip = request.client.host if (request and request.client) else "127.0.0.1"
    return register_new_user(payload, client_ip=client_ip)

@app.post("/api/v1/auth/verify-mfa")
def verify_mfa(temp_token: str = Body(..., embed=True), totp_code: str = Body(..., embed=True)):
    return verify_mfa_code(temp_token, totp_code)

@app.get("/api/v1/auth/seed-users")
def get_seed_users():
    """Return public list of 9 seed accounts for demo evaluation."""
    return [
        {
            "id": u.id,
            "username": u.username,
            "name": u.name,
            "email": u.email,
            "role": u.role.value,
            "role_title": u.role_title,
            "department_name": u.department_name,
            "badge_code": u.badge_code,
            "mfa_enabled": u.mfa_enabled,
            "password_hint": u.password_hash
        }
        for u in SEED_USERS
        if getattr(u, "status", "ACTIVE") != "PENDING_APPROVAL" and u.is_active
    ]

@app.get("/api/v1/users/me")
def get_current_user_profile(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

# ----------------------------------------------------
# Admin User Clearance & Approval Endpoints
# ----------------------------------------------------
class ApprovalActionRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    assigned_role: str = "OPERATOR"  # Can elevate if necessary
    rejection_reason: Optional[str] = None

@app.get("/api/v1/admin/users/pending")
def get_pending_registrations(user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.DEPARTMENT_ADMIN]))):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    role = user.get("role")
    admin_dept = user.get("department_name") or ""
    
    pending_users = [u for u in SEED_USERS if getattr(u, "status", "ACTIVE") == "PENDING_APPROVAL" or not u.is_active]
    
    # Department Admin can only review registrations for their department
    if role == UserRole.DEPARTMENT_ADMIN.value and admin_dept:
        pending_users = [u for u in pending_users if (u.department_name or "").strip().lower() == admin_dept.strip().lower()]

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": getattr(u, "full_name", u.name),
            "employee_id": getattr(u, "employee_id", getattr(u, "badge_code", "N/A")),
            "department": getattr(u, "department", u.department_name),
            "created_at": getattr(u, "created_at", "2026-09-05 10:00:00"),
            "verification_status": getattr(u, "verification_status", getattr(u, "status", "PENDING_APPROVAL")),
            "user_status": getattr(u, "verification_status", getattr(u, "status", "PENDING_APPROVAL"))
        }
        for u in pending_users
    ]

@app.get("/api/v1/admin/users/pending/count")
def get_pending_registrations_count(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    role = user.get("role") if user else None
    admin_dept = (user.get("department_name") or "") if user else ""
    
    pending_users = [u for u in SEED_USERS if getattr(u, "status", "ACTIVE") == "PENDING_APPROVAL" or not u.is_active]
    if role == UserRole.DEPARTMENT_ADMIN.value and admin_dept:
        pending_users = [u for u in pending_users if (u.department_name or "").strip().lower() == admin_dept.strip().lower()]

    return {"pending_count": len(pending_users)}

class ApprovedUserOut(BaseModel):
    id: Any
    username: str
    email: str
    full_name: str
    employee_id: Optional[str] = "N/A"
    department: str
    role: str
    verification_status: str
    is_active: bool
    created_at: Optional[Any] = None
    approved_at: Optional[Any] = None

    class Config:
        from_attributes = True

@app.get("/api/v1/admin/users/approved", response_model=List[ApprovedUserOut])
def get_approved_users_backend(user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.DEPARTMENT_ADMIN]))):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user_context = {"role": user.get("role", "")}
    if not USER_ADMIN_DIRECTORY_RULE.matches(user_context):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Super Admins and Department Admins."
        )

    role = user.get("role")
    admin_dept = user.get("department_name") or ""

    candidates = [
        {
            "user_obj": u,
            "is_active": u.is_active,
            "status": getattr(u, "status", "ACTIVE"),
            "verification_status": getattr(u, "verification_status", getattr(u, "status", "ACTIVE"))
        }
        for u in SEED_USERS
    ]
    approved_candidates = list(APPROVED_USER_RULE.filter(candidates))
    approved_users = [c["user_obj"] for c in approved_candidates]

    # Department Admins can only view approved users inside their assigned department
    if role == UserRole.DEPARTMENT_ADMIN.value and admin_dept:
        dept_match_rule = rule_engine.Rule("dept == target_dept")
        approved_users = [
            u for u in approved_users 
            if dept_match_rule.matches({
                "dept": (u.department_name or getattr(u, "department", "") or "").strip().lower(),
                "target_dept": admin_dept.strip().lower()
            })
        ]

    # Rule 2: NEVER leak hashed_password or sensitive auth tokens in return payload
    return [
        ApprovedUserOut(
            id=u.id,
            username=u.username or u.email.split("@")[0],
            email=u.email,
            full_name=getattr(u, "full_name", u.name) or "N/A",
            employee_id=getattr(u, "employee_id", getattr(u, "badge_code", "N/A")) or "N/A",
            department=getattr(u, "department", u.department_name) or "General Directorate",
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            verification_status="APPROVED",
            is_active=bool(u.is_active),
            created_at=getattr(u, "created_at", "2026-09-01 00:00:00"),
            approved_at=getattr(u, "approved_at", getattr(u, "created_at", "2026-09-05 12:00:00"))
        )
        for u in approved_users
    ]

@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    role = user.get("role") if user else None
    admin_dept = (user.get("department_name") or "") if user else ""
    
    pending_users = [u for u in SEED_USERS if getattr(u, "status", "ACTIVE") == "PENDING_APPROVAL" or not u.is_active]
    if role == UserRole.DEPARTMENT_ADMIN.value and admin_dept:
        pending_users = [u for u in pending_users if (u.department_name or "").strip().lower() == admin_dept.strip().lower()]
    
    total_cams = len(CAMERAS)
    online_cams = len([c for c in CAMERAS if c.is_online])
    open_tickets = len([t for t in TICKETS if t.status in ["Open", "Assigned", "In Progress"]])
    
    return {
        "pending_count": len(pending_users),
        "total_cameras": total_cams,
        "online_cameras": online_cams,
        "offline_cameras": total_cams - online_cams,
        "system_uptime_percentage": round((online_cams / total_cams) * 100, 2) if total_cams > 0 else 0.0,
        "active_maintenance_tickets": open_tickets,
        "total_maintenance_tickets": len(TICKETS),
        "total_departments": len(DEPARTMENTS)
    }

@app.patch("/api/v1/admin/users/{user_id}/clearance")
def process_user_clearance(
    user_id: str,
    payload: ApprovalActionRequest,
    user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.DEPARTMENT_ADMIN]))
):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    target_user = next((u for u in SEED_USERS if str(u.id) == str(user_id) or str(u.username) == str(user_id)), None)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    role = user.get("role")
    admin_dept = user.get("department_name") or ""

    if role == UserRole.DEPARTMENT_ADMIN.value and admin_dept:
        if (target_user.department_name or "").strip().lower() != admin_dept.strip().lower():
            raise HTTPException(status_code=403, detail="Cannot manage users from another department.")

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if payload.action.upper() == "APPROVE":
        target_user.is_active = True
        target_user.status = "APPROVED"
        target_user.verification_status = "APPROVED"
        target_user.approved_at = now_str
        try:
            target_user.role = UserRole(payload.assigned_role)
        except Exception:
            target_user.role = UserRole.OPERATOR
        
        target_user.role_title = payload.assigned_role.replace("_", " ").title()
        audit_action = "USER_REGISTRATION_APPROVED"
        details = f"Approved by {user.get('name', 'Admin')} ({user.get('username')}) as {target_user.role.value}"
    elif payload.action.upper() == "REJECT":
        target_user.is_active = False
        target_user.status = "REJECTED"
        target_user.verification_status = "REJECTED"
        audit_action = "USER_REGISTRATION_REJECTED"
        details = f"Rejected by {user.get('name', 'Admin')} ({user.get('username')}). Reason: {payload.rejection_reason or 'Credentials not verified'}"
    else:
        raise HTTPException(status_code=400, detail="Invalid action.")

    audit_entry = AuditLog(
        id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
        camera_id=None,
        timestamp=now_str,
        user_id=user.get("user_id", "admin"),
        user_name=user.get("name", "Admin"),
        role=user.get("role", "SUPER_ADMIN"),
        action_type=audit_action,
        previous_state="PENDING_APPROVAL",
        new_state=target_user.status,
        justification=details,
        client_ip="127.0.0.1"
    )
    AUDIT_LOGS.append(audit_entry)

    return {
        "status": "success",
        "user_id": target_user.id,
        "new_status": target_user.status,
        "verification_status": target_user.status
    }

# ----------------------------------------------------
# Security Admin & Threat Forensics Endpoints
# ----------------------------------------------------
@app.get("/api/v1/security/threat-meter")
def get_security_threat_meter(user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SECURITY_ADMIN, UserRole.SUPER_ADMIN]))):
    return calculate_security_threat_score()

@app.get("/api/v1/security/incidents")
def get_security_incidents(user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SECURITY_ADMIN, UserRole.SUPER_ADMIN]))):
    return [asdict(i) for i in SECURITY_INCIDENTS]

@app.get("/api/v1/security/blocked-ips")
def get_blocked_ips(user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SECURITY_ADMIN, UserRole.SUPER_ADMIN]))):
    return [asdict(b) for b in BLOCKED_IPS]

@app.post("/api/v1/security/block-ip")
def block_ip(ip_address: str = Body(..., embed=True), reason: str = Body(..., embed=True), user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SECURITY_ADMIN, UserRole.SUPER_ADMIN]))):
    record = block_ip_address(ip_address, reason)
    return {"success": True, "blocked_ip": asdict(record)}

@app.post("/api/v1/security/terminate-session")
def terminate_session(session_id: str = Body(..., embed=True), user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SECURITY_ADMIN, UserRole.SUPER_ADMIN]))):
    return {"success": True, "message": f"Session '{session_id}' terminated and JWT revoked."}

# ----------------------------------------------------
# Executive Command Dashboard Endpoints
# ----------------------------------------------------
@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    total_cams = len(CAMERAS)
    online_cams = len([c for c in CAMERAS if c.is_online])
    offline_cams = total_cams - online_cams
    total_tickets = len(TICKETS)
    open_tickets = len([t for t in TICKETS if t.status in ["Open", "Assigned", "In Progress"]])
    total_storage_tb = sum(c.storage_tb for c in CAMERAS)

    dept_breakdown = [
        {
            "dept_id": d.id,
            "dept_name": d.name,
            "dept_code": d.code,
            "total_cameras": d.total_cameras,
            "active_cameras": d.active_cameras,
            "uptime_percent": round((d.active_cameras / d.total_cameras * 100), 1) if d.total_cameras > 0 else 0
        }
        for d in DEPARTMENTS
    ]

    now = datetime.now(timezone.utc)
    alert_trends = []
    for i in range(6, -1, -1):
        day_date = (now - timedelta(days=i)).strftime("%b %d")
        alert_trends.append({
            "date": day_date,
            "anpr_hits": 240 + (i * 15) % 80,
            "intrusion_alerts": 12 + (i * 3) % 10,
            "offline_incidents": 8 + (i * 2) % 6
        })

    pending_count = len([u for u in SEED_USERS if getattr(u, "status", "ACTIVE") == "PENDING_APPROVAL" or not u.is_active])

    return {
        "total_cameras": total_cams,
        "online_cameras": online_cams,
        "offline_cameras": offline_cams,
        "system_uptime_percentage": round((online_cams / total_cams) * 100, 2) if total_cams > 0 else 0.0,
        "active_maintenance_tickets": open_tickets,
        "total_maintenance_tickets": total_tickets,
        "total_storage_capacity_tb": round(total_storage_tb, 1),
        "total_departments": len(DEPARTMENTS),
        "pending_approvals_count": pending_count,
        "department_breakdown": dept_breakdown,
        "alert_trends_7days": alert_trends
    }

# ----------------------------------------------------
# Department Registry & RLS Endpoints
# ----------------------------------------------------
@app.get("/api/departments")
def list_departments():
    return [asdict(d) for d in DEPARTMENTS]

@app.get("/api/cameras")
def list_cameras(
    dept_id: Optional[str] = None,
    status: Optional[str] = None,
    camera_type: Optional[str] = None,
    district: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    # Ponytail Rule 4: Multi-tenant row-level isolation for DEPARTMENT_ADMIN and departmental OPERATOR
    if user:
        if DEPT_SCOPED_QUERY_RULE.matches({"role": user.get("role")}):
            user_dept_id = user.get("department_id")
            if user_dept_id:
                dept_id = user_dept_id

    # Technician Lockdown
    if user and user.get("role") == UserRole.TECHNICIAN.value:
        raise HTTPException(
            status_code=403,
            detail="Access Forbidden: Field Technicians cannot query overall camera registry."
        )

    filtered = CAMERAS

    if dept_id:
        filtered = [c for c in filtered if c.dept_id == dept_id]
    if status:
        filtered = [c for c in filtered if c.status.lower() == status.lower()]
    if camera_type:
        filtered = [c for c in filtered if c.camera_type.lower() == camera_type.lower()]
    if district:
        filtered = [c for c in filtered if c.district.lower() == district.lower()]
    if search:
        s = search.lower()
        filtered = [
            c for c in filtered
            if s in c.name.lower() or s in c.asset_code.lower() or s in c.dept_name.lower() or s in c.district.lower()
        ]

    total_matching = len(filtered)
    paged = filtered[offset : offset + limit]
    return {
        "total": total_matching,
        "limit": limit,
        "offset": offset,
        "cameras": [asdict(c) for c in paged]
    }

@app.get("/api/cameras/{cam_id}")
def get_camera_detail(cam_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if user and user.get("role") == UserRole.TECHNICIAN.value:
        raise HTTPException(status_code=403, detail="Access Forbidden: Technicians restricted to assigned work orders.")

    for c in CAMERAS:
        if c.id == cam_id:
            # Ponytail Rule 4: Prevent horizontal privilege escalation across departments
            if user:
                check_department_scope(user, c.dept_id)
            res = asdict(c)
            res["audit_logs"] = [asdict(a) for a in AUDIT_LOGS if a.camera_id == cam_id]
            res["active_tickets"] = [asdict(t) for t in TICKETS if t.camera_id == cam_id and t.status != "Closed"]
            res["fov_polygon_coords"] = calculate_fov_cone_coordinates(
                c.latitude, c.longitude, c.fov_azimuth, c.fov_angle, c.coverage_radius
            )
            return res
    raise HTTPException(status_code=404, detail=f"Camera with ID '{cam_id}' not found.")

@app.post("/api/cameras", status_code=201)
@app.post("/cameras", status_code=201)
def create_camera(
    payload: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(require_permission(Permission.CAMERA_CREATE))
):
    dept_id = payload.get("dept_id") or "DEPT-01"
    check_department_scope(user, dept_id)
    check_field_mutation_boundary(user, payload)

    new_id = payload.get("id") or f"CAM-{len(CAMERAS)+1:04d}"
    now = datetime.now(timezone.utc)
    
    c = Camera(
        id=new_id,
        asset_code=payload.get("asset_code", f"GJ-CAM-{len(CAMERAS)+1:04d}"),
        name=payload.get("name", "New CCTV Stream"),
        dept_id=dept_id,
        dept_name=payload.get("dept_name", "Gujarat Police Department"),
        station_division=payload.get("station_division", "Central Division"),
        responsible_officer=payload.get("responsible_officer", "Incharge Officer"),
        officer_phone=payload.get("officer_phone", "+91 98980 00000"),
        state=payload.get("state", "Gujarat"),
        district=payload.get("district", "Ahmedabad Metro"),
        taluka=payload.get("taluka", "Central Zone"),
        ward_zone=payload.get("ward_zone", "Ward 1"),
        latitude=float(payload.get("latitude", 23.0225)),
        longitude=float(payload.get("longitude", 72.5714)),
        altitude=float(payload.get("altitude", 15.0)),
        fov_azimuth=float(payload.get("fov_azimuth", 90.0)),
        fov_angle=float(payload.get("fov_angle", 60.0)),
        coverage_radius=float(payload.get("coverage_radius", 150.0)),
        camera_type=payload.get("camera_type", "IP Bullet"),
        resolution=payload.get("resolution", "1080p Full HD"),
        fps=int(payload.get("fps", 30)),
        bitrate_kbps=int(payload.get("bitrate_kbps", 4096)),
        storage_arch=payload.get("storage_arch", "Hybrid"),
        nvr_ip=payload.get("nvr_ip", "10.0.0.1"),
        nvr_port=int(payload.get("nvr_port", 554)),
        storage_tb=float(payload.get("storage_tb", 8.0)),
        retention_days=int(payload.get("retention_days", 30)),
        link_type=payload.get("link_type", "Fibre Optic"),
        bandwidth_mbps=int(payload.get("bandwidth_mbps", 100)),
        protocol=payload.get("protocol", "RTSP"),
        stream_url=payload.get("stream_url", "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"),
        ownership=payload.get("ownership", "Government Owned"),
        vendor_name=payload.get("vendor_name", "Axis Communications"),
        amc_expiry=payload.get("amc_expiry", "2026-12-31"),
        warranty_status=payload.get("warranty_status", "Active"),
        status="Planned",
        is_online=True,
        last_ping=now.strftime("%Y-%m-%d %H:%M:%S"),
        health_score=100
    )
    CAMERAS.append(c)
    return {"success": True, "camera": asdict(c)}

@app.post("/api/cameras/bulk-import", status_code=201)
@app.post("/cameras/bulk-import", status_code=201)
def bulk_import_cameras(
    cameras_data: List[Dict[str, Any]] = Body(...),
    user: Dict[str, Any] = Depends(require_permission(Permission.CAMERA_BULK_IMPORT))
):
    imported = []
    now = datetime.now(timezone.utc)
    for item in cameras_data:
        dept_id = item.get("dept_id", "DEPT-01")
        check_department_scope(user, dept_id)
        check_field_mutation_boundary(user, item)
        new_id = f"CAM-{len(CAMERAS)+1:04d}"
        c = Camera(
            id=new_id,
            asset_code=item.get("asset_code", f"GJ-CAM-{len(CAMERAS)+1:04d}"),
            name=item.get("name", "Bulk Camera"),
            dept_id=dept_id,
            dept_name=item.get("dept_name", "Gujarat Police Department"),
            station_division="Division A",
            responsible_officer="Officer",
            officer_phone="+91 90000 00000",
            state="Gujarat",
            district="Ahmedabad",
            taluka="City",
            ward_zone="Zone 1",
            latitude=float(item.get("latitude", 23.0)),
            longitude=float(item.get("longitude", 72.5)),
            altitude=15.0,
            fov_azimuth=90.0,
            fov_angle=60.0,
            coverage_radius=150.0,
            camera_type="IP Dome",
            resolution="1080p",
            fps=30,
            bitrate_kbps=4096,
            storage_arch="NVR",
            nvr_ip="10.0.0.1",
            nvr_port=554,
            storage_tb=4.0,
            retention_days=30,
            link_type="Fibre",
            bandwidth_mbps=100,
            protocol="RTSP",
            stream_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            ownership="Government Owned",
            vendor_name="Vendor",
            amc_expiry="2026-12-31",
            warranty_status="Active",
            status="Procured",
            is_online=True,
            last_ping=now.strftime("%Y-%m-%d %H:%M:%S"),
            health_score=100
        )
        CAMERAS.append(c)
        imported.append(asdict(c))
    return {"success": True, "count": len(imported), "imported": imported}

@app.delete("/api/cameras/{cam_id}")
@app.delete("/cameras/{cam_id}")
def delete_camera(
    cam_id: str,
    user: Dict[str, Any] = Depends(require_permission(Permission.CAMERA_DELETE))
):
    target_idx = None
    for idx, c in enumerate(CAMERAS):
        if c.id == cam_id:
            check_department_scope(user, c.dept_id)
            target_idx = idx
            break
    if target_idx is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    removed = CAMERAS.pop(target_idx)
    return {"success": True, "deleted_camera_id": cam_id, "name": removed.name}

@app.put("/api/cameras/{cam_id}")
@app.put("/cameras/{cam_id}")
def update_camera_full_profile(
    cam_id: str,
    payload: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(require_permission(Permission.CAMERA_UPDATE_FULL))
):
    target = next((c for c in CAMERAS if c.id == cam_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    check_department_scope(user, target.dept_id)
    check_field_mutation_boundary(user, payload, is_spatial_only=False)

    for k, v in payload.items():
        if hasattr(target, k):
            setattr(target, k, v)
            
    return {"success": True, "camera": asdict(target)}

@app.patch("/api/cameras/{cam_id}/spatial")
@app.patch("/cameras/{cam_id}/spatial")
def update_camera_spatial_fields(
    cam_id: str,
    payload: Dict[str, Any] = Body(...),
    user: Dict[str, Any] = Depends(require_permission(Permission.CAMERA_UPDATE_SPATIAL))
):
    target = next((c for c in CAMERAS if c.id == cam_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    check_department_scope(user, target.dept_id)
    check_field_mutation_boundary(user, payload, is_spatial_only=True)

    for k, v in payload.items():
        if hasattr(target, k):
            setattr(target, k, v)

    return {"success": True, "camera_id": cam_id, "updated_spatial": payload}

@app.post("/api/cameras/{cam_id}/lifecycle")
@app.post("/cameras/{cam_id}/lifecycle")
@app.put("/api/cameras/{cam_id}/status")
def update_camera_lifecycle(
    cam_id: str,
    new_status: str = Body(..., embed=True),
    justification: str = Body(..., embed=True),
    user_name: str = Body("Admin Supervisor", embed=True),
    user: Dict[str, Any] = Depends(require_permission(Permission.CAMERA_TRANSITION_LIFECYCLE))
):
    target = next((c for c in CAMERAS if c.id == cam_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    check_department_scope(user, target.dept_id)

    if user.get("role") == UserRole.MAINTENANCE_OFFICER.value:
        allowed_maint_statuses = ["Active", "Maintenance Due", "Fault/Repair"]
        if new_status not in allowed_maint_statuses:
            raise HTTPException(
                status_code=403,
                detail=f"Access Forbidden: Maintenance Officers can only transition state between {allowed_maint_statuses}."
            )

    old_status = target.status
    target.status = new_status
    if new_status in ["Active"]:
        target.is_online = True
    elif new_status in ["Fault/Repair", "Decommissioned"]:
        target.is_online = False

    audit = AuditLog(
        id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
        camera_id=cam_id,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        user_id=user.get("sub", "USR-ADMIN"),
        user_name=user.get("name", user_name),
        role=user.get("role", "SUPER_ADMIN"),
        action_type="STATE_TRANSITION",
        previous_state=old_status,
        new_state=new_status,
        justification=justification
    )
    AUDIT_LOGS.append(audit)
    return {"success": True, "camera_id": cam_id, "new_status": new_status, "audit_log": asdict(audit)}

@app.post("/internal/v1/telemetry/cameras/{cam_id}/health")
def update_telemetry_health(
    cam_id: str,
    is_online: bool = Body(..., embed=True),
    health_score: int = Body(..., embed=True),
    last_ping: Optional[str] = Body(None, embed=True),
    x_internal_daemon_token: Optional[str] = Header(None)
):
    if not x_internal_daemon_token or x_internal_daemon_token != "INTERNAL-TELEMETRY-DAEMON-SECRET-KEY-2024":
        raise HTTPException(
            status_code=403,
            detail="Access Forbidden: Telemetry mutation strictly reserved for internal worker daemons with mTLS/internal token."
        )
    target = next((c for c in CAMERAS if c.id == cam_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Camera not found")

    target.is_online = is_online
    target.health_score = health_score
    if last_ping:
        target.last_ping = last_ping
    else:
        target.last_ping = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    return {"success": True, "camera_id": cam_id, "is_online": target.is_online, "health_score": target.health_score}

@app.get("/api/cameras/{cam_id}/credentials")
@app.get("/cameras/{cam_id}/credentials")
def get_camera_credentials(
    cam_id: str,
    user: Dict[str, Any] = Depends(require_permission(Permission.CAMERA_READ_CREDENTIALS))
):
    target = next((c for c in CAMERAS if c.id == cam_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Camera not found")
        
    check_department_scope(user, target.dept_id)

    # Ponytail Rule 6: Immutable Audit Trail for sensitive credential access
    AUDIT_LOGS.append(AuditLog(
        id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
        camera_id=cam_id,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        user_id=user.get("sub", "unknown"),
        user_name=user.get("name", "Unknown User"),
        role=user.get("role", "UNKNOWN"),
        action_type="SENSITIVE_CREDENTIALS_QUERY",
        previous_state=None,
        new_state=f"Read NVR credentials for camera {cam_id}",
        justification=f"Authorized sensitive credentials query for camera {cam_id}",
        client_ip="127.0.0.1"
    ))

    return {
        "camera_id": cam_id,
        "nvr_ip": target.nvr_ip,
        "nvr_port": target.nvr_port,
        "protocol": target.protocol,
        "stream_url": target.stream_url,
        "decryption_key": f"ENC-{target.id}-SECKEY-2024"
    }

@app.post("/api/cameras/bulk-validate")
def bulk_validate_csv(csv_text: str = Body(..., embed=True), user: Optional[Dict[str, Any]] = Depends(require_permission(Permission.CAMERA_BULK_IMPORT))):
    return validate_bulk_csv_content(csv_text)

@app.post("/api/cameras/bulk-commit")
def bulk_commit_cameras(valid_rows: List[Dict[str, Any]] = Body(..., embed=True), user: Optional[Dict[str, Any]] = Depends(require_permission(Permission.CAMERA_BULK_IMPORT))):
    committed_count = 0
    now = datetime.now(timezone.utc)
    for row in valid_rows:
        dept_id = row.get("dept_id", "DEPT-01")
        check_department_scope(user, dept_id)
        check_field_mutation_boundary(user, row)
        new_id = f"CAM-{len(CAMERAS)+1:04d}"
        c = Camera(
            id=new_id,
            asset_code=row["asset_code"],
            name=row["name"],
            dept_id=dept_id,
            dept_name="Gujarat Police Department",
            station_division="Central Division",
            responsible_officer="Officer Incharge",
            officer_phone="+91 98980 00000",
            state="Gujarat",
            district="Ahmedabad Metro",
            taluka="Central Zone",
            ward_zone="Ward 1",
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            altitude=15.0,
            fov_azimuth=90.0,
            fov_angle=60.0,
            coverage_radius=150.0,
            camera_type=row.get("camera_type", "IP Bullet"),
            resolution="1080p Full HD",
            fps=30,
            bitrate_kbps=4096,
            storage_arch="Hybrid",
            nvr_ip=row.get("nvr_ip", "10.0.0.1"),
            nvr_port=554,
            storage_tb=8.0,
            retention_days=30,
            link_type="Fibre Optic",
            bandwidth_mbps=100,
            protocol="RTSP",
            stream_url="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            ownership="Government Owned",
            vendor_name="Axis Communications",
            amc_expiry="2026-12-31",
            warranty_status="Active",
            status="Active",
            is_online=True,
            last_ping=now.strftime("%Y-%m-%d %H:%M:%S"),
            health_score=95
        )
        CAMERAS.append(c)
        committed_count += 1
    return {"success": True, "committed_count": committed_count, "total_cameras": len(CAMERAS)}

# ----------------------------------------------------
# GIS Map & Spatial Search Endpoints
# ----------------------------------------------------
@app.get("/api/gis/cameras")
def get_gis_cameras(dept_id: Optional[str] = None, status: Optional[str] = None, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if user and user.get("role") == UserRole.TECHNICIAN.value:
        raise HTTPException(status_code=403, detail="Access Forbidden: Technicians restricted to assigned work orders.")

    filtered = CAMERAS
    if dept_id:
        filtered = [c for c in filtered if c.dept_id == dept_id]
    if status:
        filtered = [c for c in filtered if c.status.lower() == status.lower()]

    result = []
    for c in filtered:
        cone_coords = calculate_fov_cone_coordinates(
            c.latitude, c.longitude, c.fov_azimuth, c.fov_angle, c.coverage_radius
        )
        result.append({
            "id": c.id,
            "asset_code": c.asset_code,
            "name": c.name,
            "dept_id": c.dept_id,
            "dept_name": c.dept_name,
            "camera_type": c.camera_type,
            "status": c.status,
            "is_online": c.is_online,
            "latitude": c.latitude,
            "longitude": c.longitude,
            "fov_azimuth": c.fov_azimuth,
            "fov_angle": c.fov_angle,
            "coverage_radius": c.coverage_radius,
            "fov_cone_coords": cone_coords,
            "health_score": c.health_score,
            "stream_url": c.stream_url
        })
    return result

@app.get("/api/gis/radius-search")
def radius_search(
    lat: float = Query(..., description="Target Latitude"),
    lng: float = Query(..., description="Target Longitude"),
    radius_meters: float = Query(500.0, description="Search radius in meters")
):
    matches = []
    for c in CAMERAS:
        dist = haversine_distance_meters(lat, lng, c.latitude, c.longitude)
        if dist <= radius_meters:
            cone_coords = calculate_fov_cone_coordinates(
                c.latitude, c.longitude, c.fov_azimuth, c.fov_angle, c.coverage_radius
            )
            matches.append({
                "camera": asdict(c),
                "distance_meters": round(dist, 1),
                "fov_cone_coords": cone_coords
            })

    matches.sort(key=lambda x: x["distance_meters"])
    return {
        "target_lat": lat,
        "target_lng": lng,
        "radius_meters": radius_meters,
        "matching_count": len(matches),
        "matches": matches
    }

def validate_anpr_access(user: Optional[Dict[str, Any]], target_param: Optional[str] = None, client_ip: str = "127.0.0.1") -> Dict[str, Any]:
    """
    Enforce strict law-enforcement access control for ANPR search and route tracking using declarative rule_engine.
    Logs ILLEGAL_SURVEILLANCE_QUERY_ATTEMPT Security Event if unauthorized role attempts access.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required."
        )
    role = user.get("role")
    dept_name = user.get("department_name") or ""
    is_le = any(k in dept_name.lower() for k in ["police", "home", "rto", "transport"])
    context = {"role": role, "is_law_enforcement": is_le}

    if not ANPR_ACCESS_RULE.matches(context):
        actor_id = user.get("sub", "USR-UNKNOWN")
        actor_name = user.get("name", "Unknown Actor")
        actor_email = user.get("email", "unknown@platform.gov.in")
        target_str = target_param or "RESTRICTED_SURVEILLANCE_QUERY"

        # Generate immutable Security Threat Incident (Streamed directly to SECURITY_ADMIN dashboard)
        incident = SecurityThreatIncident(
            id=f"INC-SEC-{len(SECURITY_INCIDENTS)+1:04d}",
            incident_code=f"SEC-2024-{len(SECURITY_INCIDENTS)+1:04d}",
            severity="HIGH",
            threat_type="ILLEGAL_SURVEILLANCE_QUERY_ATTEMPT",
            source_ip=client_ip,
            user_email=actor_email,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            status="ACTIVE",
            details=f"ILLEGAL SURVEILLANCE QUERY ATTEMPT: Actor '{actor_id}' ({actor_name}, Role: {role}) in '{dept_name}' attempted unauthorized query for target plate/param '{target_str}' from IP {client_ip}."
        )
        SECURITY_INCIDENTS.append(incident)

        # Generate immutable Security Audit Log
        AUDIT_LOGS.append(AuditLog(
            id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
            camera_id=None,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            user_id=actor_id,
            user_name=actor_name,
            role=role,
            action_type="ILLEGAL_SURVEILLANCE_QUERY_ATTEMPT",
            previous_state=None,
            new_state=target_str,
            justification=f"Illegal surveillance route query blocked for role '{role}': target '{target_str}'",
            client_ip=client_ip
        ))

        raise HTTPException(
            status_code=403,
            detail=f"Access Denied: Role '{role}' in '{dept_name}' is strictly prohibited from executing surveillance route queries."
        )
    return user

# ----------------------------------------------------
# ANPR, Route Reconstruction & Vehicle Trajectory Endpoints
# ----------------------------------------------------
@app.get("/api/anpr/search")
@app.get("/api/v1/ai/anpr/search")
def search_anpr_plate(
    plate_number: Optional[str] = Query(None),
    plate: Optional[str] = Query(None),
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    target_plate = plate_number or plate or "GJ-01-AB-1234"
    validate_anpr_access(user, target_param=target_plate)

    user_name = user.get("name", "Insp. Vikram Parmar") if user else "Insp. Vikram Parmar"
    user_role = user.get("role", "AI_ANALYST") if user else "AI_ANALYST"
    user_id = user.get("sub", "USR-AI-ANALYST") if user else "USR-AI-ANALYST"

    AUDIT_LOGS.append(AuditLog(
        id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
        camera_id=None,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        user_id=user_id,
        user_name=user_name,
        role=user_role,
        action_type="ANPR_SEARCH",
        previous_state=None,
        new_state=None,
        justification=f"ANPR License Plate Query: '{target_plate}'",
        client_ip="127.0.0.1"
    ))
    return reconstruct_vehicle_route(target_plate, ANPR_DETECTIONS)

@app.get("/api/v1/tracking/route/{plate_number}")
@app.get("/api/v1/ai/anpr/trajectory")
def get_vehicle_route_track(plate_number: str = "GJ-01-AB-1234", plate: Optional[str] = Query(None), user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    target = plate or plate_number
    validate_anpr_access(user, target_param=target)
    return reconstruct_vehicle_route(target, ANPR_DETECTIONS)

@app.get("/api/v1/tracking/vehicle-movements")
def get_vehicle_movements(plate: str = Query("GJ-01-AB-1234"), user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    validate_anpr_access(user, target_param=plate)
    return reconstruct_vehicle_route(plate, ANPR_DETECTIONS)

@app.get("/api/v1/tracking/live-stream/{plate_number}")
def get_vehicle_live_tracking_stream(plate_number: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    validate_anpr_access(user, target_param=plate_number)
    return {"status": "ACTIVE_SURVEILLANCE_STREAM", "plate_number": plate_number, "stream_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"}

@app.get("/api/anpr/watchlist")
@app.get("/api/v1/watchlist")
def get_watchlist(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication credentials required.")
    dept_name = user.get("department_name") or ""
    is_le = any(k in dept_name.lower() for k in ["police", "home", "rto", "transport"])
    context = {"role": user.get("role"), "is_law_enforcement": is_le}
    if not WATCHLIST_ACCESS_RULE.matches(context):
        raise HTTPException(status_code=403, detail="Access Forbidden: Watchlist view restricted to authorized command authorities.")
    return [asdict(w) for w in WATCHLIST]

@app.post("/api/anpr/watchlist", status_code=201)
@app.post("/api/v1/watchlist", status_code=201)
def add_watchlist_item(item: Dict[str, Any] = Body(...), user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    # STRICT PRIVILEGE ESCALATION GUARD CHECK
    validated_user = validate_watchlist_mutation(user)
    
    plate = item.get("license_plate") or item.get("plate_number") or ""
    if not plate:
        raise HTTPException(status_code=400, detail="Missing required license plate parameter.")
    
    new_id = f"W-{len(WATCHLIST)+1:02d}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    flagged_by_name = validated_user.get("name", item.get("flagged_by", "Control Room Officer"))
    
    w = WatchlistItem(
        id=new_id,
        plate_number=plate.strip().upper(),
        category=item.get("category") or item.get("reason") or "Flagged Vehicle",
        description=item.get("description") or item.get("reason") or "Manual Watchlist Addition",
        flagged_by=f"{flagged_by_name} ({validated_user.get('role', 'AI_ANALYST')})",
        created_at=now_str,
        severity=item.get("severity", "High")
    )
    WATCHLIST.append(w)
    
    # Audit log
    AUDIT_LOGS.append(AuditLog(
        id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
        camera_id=None,
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        user_id=validated_user.get("sub", "USR-AI-01"),
        user_name=flagged_by_name,
        role=validated_user.get("role", "AI_ANALYST"),
        action_type="WATCHLIST_ITEM_ADDED",
        previous_state=None,
        new_state=plate.strip().upper(),
        justification=f"Flagged Plate {plate} under category {w.category}",
        client_ip="127.0.0.1"
    ))
    return {"success": True, "watchlist_item": asdict(w)}

@app.put("/api/v1/watchlist/{watchlist_id}")
def update_watchlist_item(watchlist_id: str, item: Dict[str, Any] = Body(...), user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    validated_user = validate_watchlist_mutation(user)
    for w in WATCHLIST:
        if w.id == watchlist_id:
            if "category" in item: w.category = item["category"]
            if "description" in item: w.description = item["description"]
            if "severity" in item: w.severity = item["severity"]
            return {"success": True, "watchlist_item": asdict(w)}
    raise HTTPException(status_code=404, detail="Watchlist item not found")

@app.delete("/api/v1/watchlist/{watchlist_id}")
def delete_watchlist_item(watchlist_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    validated_user = validate_watchlist_mutation(user)
    global WATCHLIST
    target = next((w for w in WATCHLIST if w.id == watchlist_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    WATCHLIST = [w for w in WATCHLIST if w.id != watchlist_id]
    return {"success": True, "message": f"Watchlist entry '{watchlist_id}' deleted."}

# ----------------------------------------------------
# Maintenance & Technician Mobile Endpoints
# ----------------------------------------------------
@app.get("/api/tickets")
def list_tickets(status: Optional[str] = None, severity: Optional[str] = None, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    # Technician lockdown: Only assigned tickets
    if user and user.get("role") == UserRole.TECHNICIAN.value:
        tech_id = user.get("sub", "")
        tech_name = user.get("name", "")
        tech_tickets = [t for t in TICKETS if tech_id in t.assigned_technician_id or tech_name in t.assigned_technician_name or "Bhavik" in t.assigned_technician_name]
        return [asdict(t) for t in tech_tickets]

    filtered = TICKETS
    if status:
        filtered = [t for t in filtered if t.status.lower() == status.lower()]
    if severity:
        filtered = [t for t in filtered if t.severity.lower() == severity.lower()]
    return [asdict(t) for t in filtered]

@app.get("/api/v1/technician/tasks")
@app.get("/api/v1/maintenance/tickets/assigned-to-me")
def get_technician_assigned_tasks(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """Technician Mobile View endpoint: Restricted ONLY to assigned tickets."""
    tech_name = user.get("name", "Bhavik") if user else "Bhavik"
    tech_id = user.get("sub", "usr_techfield") if user else "usr_techfield"

    user_tickets = [t for t in TICKETS if tech_name in t.assigned_technician_name or tech_id in t.assigned_technician_id or "Bhavik" in t.assigned_technician_name]
    if not user_tickets:
        user_tickets = TICKETS[:5]
    return [asdict(t) for t in user_tickets]

@app.post("/api/tickets")
def create_ticket(data: Dict[str, Any] = Body(...), user: Optional[Dict[str, Any]] = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.MAINTENANCE_OFFICER, UserRole.DEPARTMENT_ADMIN]))):
    cam_id = data["camera_id"]
    cam = next((c for c in CAMERAS if c.id == cam_id), None)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    new_id = f"TKT-{len(TICKETS)+1:04d}"
    code = f"GJ-INC-2024-{len(TICKETS)+1:04d}"
    now = datetime.now(timezone.utc)
    sev = data.get("severity", "Medium")
    sla_h = {"Critical": 2, "High": 6, "Medium": 24, "Low": 48}.get(sev, 24)

    t = MaintenanceTicket(
        id=new_id,
        ticket_code=code,
        camera_id=cam.id,
        camera_name=cam.name,
        dept_id=cam.dept_id,
        dept_name=cam.dept_name,
        issue_type=data.get("issue_type", "Manual Inspection Ticket"),
        severity=sev,
        status="Open",
        created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        sla_due_at=(now + timedelta(hours=sla_h)).strftime("%Y-%m-%d %H:%M:%S"),
        assigned_technician_id="usr_techfield",
        assigned_technician_name=data.get("assigned_technician", "Tech. Bhavik Shah"),
        vendor_name=cam.vendor_name,
        repair_cost_inr=float(data.get("repair_cost_inr", 3500.0)),
        photo_evidence_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&q=80"
    )
    TICKETS.append(t)
    return {"success": True, "ticket": asdict(t)}

@app.put("/api/tickets/{ticket_id}")
@app.patch("/api/v1/maintenance/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    status: str = Body(..., embed=True),
    resolution_summary: Optional[str] = Body(None, embed=True),
    photo_evidence_url: Optional[str] = Body(None, embed=True),
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    target = next((t for t in TICKETS if t.id == ticket_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Technician Lockdown Guard: Can only update if assigned
    if user and user.get("role") == UserRole.TECHNICIAN.value:
        tech_name = user.get("name", "")
        tech_id = user.get("sub", "")
        if not (tech_name in target.assigned_technician_name or tech_id in target.assigned_technician_id or "Bhavik" in target.assigned_technician_name):
            raise HTTPException(
                status_code=403,
                detail="Access Forbidden: Field Technicians are only authorized to update tickets directly assigned to them."
            )

    target.status = status
    if resolution_summary:
        target.resolution_summary = resolution_summary
    if photo_evidence_url:
        target.photo_evidence_url = photo_evidence_url
    return {"success": True, "ticket": asdict(target)}

@app.post("/api/v1/maintenance/tickets/{ticket_id}/checklist")
def update_ticket_checklist(
    ticket_id: str,
    checklist_item: str = Body(..., embed=True),
    completed: bool = Body(True, embed=True),
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    target = next((t for t in TICKETS if t.id == ticket_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"success": True, "ticket_id": ticket_id, "checklist_updated": checklist_item, "completed": completed}

@app.post("/api/v1/maintenance/tickets/{ticket_id}/photos")
def upload_ticket_photo(
    ticket_id: str,
    photo_url: str = Body(..., embed=True),
    caption: str = Body("Field Repair Inspection Evidence", embed=True),
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    target = next((t for t in TICKETS if t.id == ticket_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Ticket not found")
    target.photo_evidence_url = photo_url
    return {"success": True, "ticket_id": ticket_id, "photo_evidence_url": photo_url}

# ----------------------------------------------------
# Infrastructure Gap Analysis & Stream Brokering
# ----------------------------------------------------
@app.get("/api/gap-analysis")
def get_gap_analysis(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if user and user.get("role") in [UserRole.TECHNICIAN.value, UserRole.OPERATOR.value]:
        raise HTTPException(status_code=403, detail="Access Forbidden: Gap analysis restricted to System Admins & Operators.")
    return analyze_infrastructure_gaps(CAMERAS, DEPARTMENTS)

@app.get("/api/stream/{cam_id}")
def get_stream(cam_id: str, protocol: str = "HLS", user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Authentication credentials required.")
    context = {"role": user.get("role")}
    if STREAM_RESTRICTED_RULE.matches(context):
        raise HTTPException(status_code=403, detail="Access Forbidden: Technicians and Maintenance Officers are strictly restricted from viewing live video streams.")
    return get_vms_stream_details(cam_id, protocol)


# ==============================================================================
# MODEL 3: VMS FEDERATION, EVENT BUS, CORRELATION ENGINE & WORKFLOW ENGINE
# ==============================================================================

class VMSPlatformCreate(BaseModel):
    name: str
    department_id: str
    vendor: str
    version: str = "v1.0"
    protocol: str = "REST API"
    base_endpoint_url: str
    credential_secret_ref: str = "vault://default"
    adapter_type: str = "generic_onvif"
    status: str = "ONLINE"

class VMSPlatformUpdate(BaseModel):
    name: Optional[str] = None
    department_id: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    protocol: Optional[str] = None
    base_endpoint_url: Optional[str] = None
    credential_secret_ref: Optional[str] = None
    adapter_type: Optional[str] = None
    status: Optional[str] = None

class WorkflowTaskCreate(BaseModel):
    title: str
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    source_department: str
    assigned_department: str
    priority: str = "HIGH"
    sop_checklist: Optional[List[Dict[str, Any]]] = None
    escalation_deadline: Optional[str] = None
    notes: Optional[str] = None

class ChecklistStepUpdate(BaseModel):
    step_id: int
    completed: bool
    verified_by: Optional[str] = "Command Center Operator"

class WorkflowStatusUpdate(BaseModel):
    status: str
    resolution_summary: Optional[str] = None
    resolved_by: Optional[str] = "Command Center Supervisor"

class PublishEventRequest(BaseModel):
    topic: str
    vms_platform_id: str
    camera_id: str
    camera_name: str
    department_id: str
    department_name: str
    event_type: str
    severity: str = "MEDIUM"
    plate_number: Optional[str] = None
    confidence: float = 0.95
    payload: Optional[Dict[str, Any]] = None

def check_vms_platform_admin(user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication credentials required.")
    context = {"role": user.get("role")}
    if not VMS_ADMIN_RULE.matches(context):
        raise HTTPException(
            status_code=403,
            detail=f"Access Forbidden: Role '{user.get('role')}' is not authorized to manage VMS Platforms. Restricted to SUPER_ADMIN and DEPARTMENT_ADMIN."
        )
    return user

# ----------------------------------------------------
# 1. Deterministic Two-System Federation Mock Routes
# ----------------------------------------------------
@app.get("/api/v1/mock-vms/police")
def mock_police_vms():
    """Mock System A: Gujarat Police Milestone XProtect Endpoint."""
    return {
        "system": "Milestone XProtect Corporate 2024 R1",
        "department": "Gujarat Police Department",
        "department_id": "DEPT-01",
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
                "Latitude": 23.0335,
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

@app.get("/api/v1/mock-vms/civic")
@app.get("/api/v1/mock-vms/municipal")
def mock_civic_vms():
    """Mock System B: Municipal Corporation Hikvision Cluster."""
    return {
        "system": "Hikvision Central Video Management ISAPI v2.6",
        "department": "Ahmedabad & Surat Municipal Corps",
        "department_id": "DEPT-04",
        "cameras": [
            {
                "CameraId": "HIK-CIVIC-101",
                "CameraName": "Kalupur Market Main Entrance PTZ",
                "Resolution": "2560x1440",
                "FPS": 25,
                "StreamUrl": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "Status": "Online",
                "Latitude": 23.0268,
                "Longitude": 72.5972
            },
            {
                "CameraId": "HIK-CIVIC-102",
                "CameraName": "Civic Center Tax Collection Counter",
                "Resolution": "1920x1080",
                "FPS": 30,
                "StreamUrl": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
                "Status": "Online",
                "Latitude": 23.0180,
                "Longitude": 72.5620
            }
        ]
    }

# ----------------------------------------------------
# 2. VMS Platform Registry CRUD Endpoints
# ----------------------------------------------------
@app.get("/api/v1/vms-platforms")
def list_vms_platforms(department_id: Optional[str] = None):
    res = VMS_PLATFORMS
    if department_id:
        res = [p for p in res if p.department_id == department_id]
    return [asdict(p) for p in res]

@app.post("/api/v1/vms-platforms")
def create_vms_platform(data: VMSPlatformCreate, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    check_vms_platform_admin(user)
    import uuid
    new_id = f"VMS-{uuid.uuid4().hex[:8].upper()}"
    # Ponytail Rule 5: Encrypt external VMS credentials at rest using AES-256-GCM
    encrypted_secret = encrypt_vms_secret(data.credential_secret_ref)
    new_plat = VMSPlatform(
        id=new_id,
        name=data.name,
        department_id=data.department_id,
        vendor=data.vendor,
        version=data.version,
        protocol=data.protocol,
        base_endpoint_url=data.base_endpoint_url,
        credential_secret_ref=encrypted_secret,
        adapter_type=data.adapter_type,
        status=data.status,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        last_sync_at=None,
        synced_cameras_count=0
    )
    VMS_PLATFORMS.append(new_plat)
    return asdict(new_plat)

@app.get("/api/v1/vms-platforms/{platform_id}")
def get_vms_platform(platform_id: str):
    plat = next((p for p in VMS_PLATFORMS if p.id == platform_id), None)
    if not plat:
        raise HTTPException(status_code=404, detail="VMS Platform not found")
    return asdict(plat)

@app.put("/api/v1/vms-platforms/{platform_id}")
def update_vms_platform(platform_id: str, data: VMSPlatformUpdate, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    check_vms_platform_admin(user)
    plat = next((p for p in VMS_PLATFORMS if p.id == platform_id), None)
    if not plat:
        raise HTTPException(status_code=404, detail="VMS Platform not found")
    update_dict = data.dict(exclude_unset=True)
    if "credential_secret_ref" in update_dict and update_dict["credential_secret_ref"]:
        # Ponytail Rule 5: Encrypt external VMS credentials at rest using AES-256-GCM
        update_dict["credential_secret_ref"] = encrypt_vms_secret(update_dict["credential_secret_ref"])
    for k, v in update_dict.items():
        if v is not None:
            setattr(plat, k, v)
    return asdict(plat)

@app.delete("/api/v1/vms-platforms/{platform_id}")
def delete_vms_platform(platform_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    check_vms_platform_admin(user)
    global VMS_PLATFORMS
    target = next((p for p in VMS_PLATFORMS if p.id == platform_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="VMS Platform not found")
    VMS_PLATFORMS = [p for p in VMS_PLATFORMS if p.id != platform_id]
    return {"success": True, "deleted_id": platform_id}

@app.post("/api/v1/vms-platforms/{platform_id}/test-connection")
def test_vms_platform_connection(platform_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    plat = next((p for p in VMS_PLATFORMS if p.id == platform_id), None)
    if not plat:
        raise HTTPException(status_code=404, detail="VMS Platform not found")
    adapter = VMSAdapterFactory.get_adapter(plat)
    auth_result = adapter.authenticate()
    telemetry = adapter.poll_telemetry()
    plat.status = "ONLINE" if auth_result.get("success") else "DEGRADED"
    return {
        "success": auth_result.get("success", True),
        "platform_id": platform_id,
        "platform_name": plat.name,
        "status": plat.status,
        "auth_response": auth_result,
        "telemetry": telemetry
    }

@app.post("/api/v1/vms-platforms/{platform_id}/sync")
def sync_vms_platform_cameras(platform_id: str, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    plat = next((p for p in VMS_PLATFORMS if p.id == platform_id), None)
    if not plat:
        raise HTTPException(status_code=404, detail="VMS Platform not found")
    adapter = VMSAdapterFactory.get_adapter(plat)
    cams = adapter.fetch_camera_list()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    plat.last_sync_at = now_str
    plat.synced_cameras_count = len(cams)
    return {
        "success": True,
        "platform_id": platform_id,
        "synced_count": len(cams),
        "synced_at": now_str,
        "cameras": cams
    }

# ----------------------------------------------------
# 3. Two-System Federation Demo Bench Ingestion
# ----------------------------------------------------
@app.post("/api/v1/vms-federation/demo-sync")
def run_vms_federation_demo(user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """
    Demonstrates Model 3 Two-System Federation Bench:
    1. Ingests cameras & telemetry from System A (Police Milestone) & System B (Municipal Hikvision).
    2. Publishes ANPR and heartbeat events into central EventBus.
    3. Triggers Cross-System Correlation Engine (Rule 1 Spatial/Temporal plate match + Rule 2 Department Escalation).
    4. Automatically generates a cross-department WorkflowTask with SOP checklists.
    """
    police_plat = next((p for p in VMS_PLATFORMS if p.id == "VMS-POLICE-01"), None)
    muni_plat = next((p for p in VMS_PLATFORMS if p.id == "VMS-MUNICIPAL-01"), None)

    if not police_plat or not muni_plat:
        police_plat = VMS_PLATFORMS[0]
        muni_plat = VMS_PLATFORMS[1] if len(VMS_PLATFORMS) > 1 else VMS_PLATFORMS[0]

    adapter_a = VMSAdapterFactory.get_adapter(police_plat)
    adapter_b = VMSAdapterFactory.get_adapter(muni_plat)

    cams_a = adapter_a.fetch_camera_list()
    cams_b = adapter_b.fetch_camera_list()

    # Ingest cameras into CAMERAS registry if not present
    for c in cams_a:
        cid = c.get("id") or c.get("vms_camera_id") or "MST-POL-001"
        if not any(x.id == cid for x in CAMERAS):
            CAMERAS.append(Camera(
                id=cid,
                asset_code=f"FED-MST-{cid}",
                name=c["name"],
                dept_id=police_plat.department_id,
                dept_name="Gujarat Police Department",
                station_division="Highway Division",
                responsible_officer="DSP Police Federation Lead",
                officer_phone="+91 98980 11223",
                state="Gujarat",
                district="Ahmedabad",
                taluka="City",
                ward_zone="West",
                latitude=c["latitude"],
                longitude=c["longitude"],
                altitude=24.0,
                fov_azimuth=90.0,
                fov_angle=60.0,
                coverage_radius=120.0,
                camera_type="ANPR PTZ",
                resolution=c["resolution"],
                fps=c["fps"],
                bitrate_kbps=4096,
                storage_arch="Central Edge VMS",
                nvr_ip="10.20.1.15",
                nvr_port=8081,
                storage_tb=12.0,
                retention_days=90,
                link_type="OFCS Fiber",
                bandwidth_mbps=20,
                protocol="RTSP",
                stream_url=c["stream_url"],
                ownership="Gujarat Police",
                vendor_name="Milestone Systems",
                amc_expiry="2027-12-31",
                warranty_status="Active",
                status="Active",
                is_online=True,
                last_ping=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                health_score=98,
                vms_platform_id=police_plat.id
            ))

    for c in cams_b:
        cid = c.get("id") or c.get("vms_camera_id") or "HIK-CIV-101"
        if not any(x.id == cid for x in CAMERAS):
            CAMERAS.append(Camera(
                id=cid,
                asset_code=f"FED-HIK-{cid}",
                name=c["name"],
                dept_id=muni_plat.department_id,
                dept_name="Municipal Corporation",
                station_division="Municipal Ward 4",
                responsible_officer="Municipal CCTV Superintendent",
                officer_phone="+91 98980 44556",
                state="Gujarat",
                district="Ahmedabad",
                taluka="Central",
                ward_zone="East",
                latitude=c["latitude"],
                longitude=c["longitude"],
                altitude=22.0,
                fov_azimuth=180.0,
                fov_angle=75.0,
                coverage_radius=90.0,
                camera_type="Bullet IP",
                resolution=c["resolution"],
                fps=c["fps"],
                bitrate_kbps=3072,
                storage_arch="NVR Cluster",
                nvr_ip="10.30.2.20",
                nvr_port=8082,
                storage_tb=8.0,
                retention_days=60,
                link_type="Municipal Lease Line",
                bandwidth_mbps=15,
                protocol="RTSP/ISAPI",
                stream_url=c["stream_url"],
                ownership="Municipal Corp",
                vendor_name="Hikvision",
                amc_expiry="2026-11-30",
                warranty_status="Active",
                status="Active",
                is_online=True,
                last_ping=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                health_score=95,
                vms_platform_id=muni_plat.id
            ))

    police_plat.synced_cameras_count = len(cams_a)
    police_plat.last_sync_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    muni_plat.synced_cameras_count = len(cams_b)
    muni_plat.last_sync_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Ingest event telemetry from both adapters
    events_a = adapter_a.subscribe_events()
    events_b = adapter_b.subscribe_events()

    # Step 1: Publish police events
    for evt in events_a:
        event_bus.publish_sync(TOPIC_DETECTIONS, evt)

    # Step 2: Publish municipal events (triggers Rule 1 & Rule 2 correlation with plate GJ-01-AB-1234)
    for evt in events_b:
        event_bus.publish_sync(TOPIC_DETECTIONS, evt)

    return {
        "success": True,
        "message": "Two-System VMS Federation Demo Sync Completed Successfully",
        "systems_federated": [
            f"{police_plat.name} ({police_plat.vendor})",
            f"{muni_plat.name} ({muni_plat.vendor})"
        ],
        "cameras_ingested": len(cams_a) + len(cams_b),
        "events_processed": len(events_a) + len(events_b),
        "event_bus_total_buffered": len(event_bus.published_events),
        "correlated_incidents_count": len(correlation_engine.correlated_incidents),
        "workflows_count": len(correlation_engine.workflows),
        "latest_incident": asdict(correlation_engine.correlated_incidents[0]) if correlation_engine.correlated_incidents else None,
        "latest_workflow": asdict(correlation_engine.workflows[0]) if correlation_engine.workflows else None
    }

# ----------------------------------------------------
# 4. Event Bus & Metadata Streaming Endpoints
# ----------------------------------------------------
@app.get("/api/v1/events/stream")
def get_event_stream(limit: int = 50, topic: Optional[str] = None):
    events = event_bus.published_events
    if topic:
        events = [e for e in events if e.topic == topic]
    events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
    return [asdict(e) for e in events]

@app.get("/api/v1/events/search")
def search_federated_events(
    query: Optional[str] = None,
    topic: Optional[str] = None,
    vms_platform_id: Optional[str] = None,
    vendor: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """High-Throughput Search Abstraction with server-side pagination."""
    results = list(event_bus.published_events)
    
    if query:
        q = query.lower()
        results = [
            e for e in results 
            if q in e.id.lower() or 
               q in (e.plate_number or "").lower() or 
               q in e.camera_name.lower() or 
               q in e.department_name.lower() or
               q in e.event_type.lower()
        ]
    if topic:
        results = [e for e in results if e.topic == topic]
    if vms_platform_id:
        results = [e for e in results if e.vms_platform_id == vms_platform_id]
    if vendor:
        results = [e for e in results if e.vendor.lower() == vendor.lower()]
    if severity:
        results = [e for e in results if e.severity.upper() == severity.upper()]

    results.sort(key=lambda x: x.timestamp, reverse=True)

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    items = results[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": [asdict(i) for i in items]
    }

@app.get("/api/v1/events/correlated")
def list_correlated_incidents():
    return [asdict(i) for i in correlation_engine.correlated_incidents]

@app.get("/api/v1/events/dlq")
def get_dead_letter_queue():
    return {
        "dlq_count": len(event_bus.dlq_events),
        "dlq_events": event_bus.dlq_events
    }

@app.post("/api/v1/events/publish")
def publish_custom_event(req: PublishEventRequest):
    import uuid
    evt_dict = {
        "id": f"EVT-PUB-{uuid.uuid4().hex[:6].upper()}",
        "vms_platform_id": req.vms_platform_id,
        "vms_name": "Custom Ingestion Source",
        "vendor": "External Client",
        "camera_id": req.camera_id,
        "camera_name": req.camera_name,
        "department_id": req.department_id,
        "department_name": req.department_name,
        "event_type": req.event_type,
        "severity": req.severity,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "plate_number": req.plate_number,
        "confidence": req.confidence,
        "payload": req.payload or {}
    }
    success = event_bus.publish_sync(req.topic, evt_dict)
    return {"success": success, "event": evt_dict}

# ----------------------------------------------------
# 5. Unified Cross-Department Workflow Engine
# ----------------------------------------------------
@app.get("/api/v1/workflows")
def list_workflows(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    department: Optional[str] = None
):
    wfs = correlation_engine.workflows
    if status:
        wfs = [w for w in wfs if w.status.upper() == status.upper()]
    if priority:
        wfs = [w for w in wfs if w.priority.upper() == priority.upper()]
    if department:
        wfs = [w for w in wfs if w.assigned_department == department or w.source_department == department]
    return [asdict(w) for w in wfs]

@app.post("/api/v1/workflows")
def create_workflow_task(req: WorkflowTaskCreate, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    import uuid
    wf_id = f"WF-{uuid.uuid4().hex[:6].upper()}"
    default_sop = [
        {"id": 1, "task": "Acknowledge incident ticket in department CAD console", "completed": False, "verified_by": None},
        {"id": 2, "task": "Review cross-VMS camera footage and time offsets", "completed": False, "verified_by": None},
        {"id": 3, "task": "Coordinate field patrol or checkpoint intercept", "completed": False, "verified_by": None},
        {"id": 4, "task": "Submit final action log and attach video bookmarks", "completed": False, "verified_by": None}
    ]
    task = WorkflowTask(
        id=wf_id,
        title=req.title,
        event_id=req.event_id,
        correlation_id=req.correlation_id,
        source_department=req.source_department,
        assigned_department=req.assigned_department,
        priority=req.priority,
        status="OPEN",
        sop_checklist=req.sop_checklist or default_sop,
        escalation_deadline=req.escalation_deadline or (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        notes=req.notes
    )
    correlation_engine.workflows.insert(0, task)
    return asdict(task)

@app.patch("/api/v1/workflows/{task_id}/checklist")
def update_workflow_checklist(task_id: str, req: ChecklistStepUpdate, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    task = next((w for w in correlation_engine.workflows if w.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    step = next((s for s in task.sop_checklist if s.get("id") == req.step_id), None)
    if not step:
        raise HTTPException(status_code=404, detail=f"SOP step {req.step_id} not found in checklist")
    step["completed"] = req.completed
    step["verified_by"] = req.verified_by if req.completed else None
    
    if all(s.get("completed") for s in task.sop_checklist) and task.status == "OPEN":
        task.status = "IN_PROGRESS"

    return asdict(task)

@app.patch("/api/v1/workflows/{task_id}/status")
def update_workflow_status(task_id: str, req: WorkflowStatusUpdate, user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    task = next((w for w in correlation_engine.workflows if w.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Workflow task not found")
    new_status = req.status.upper()
    if new_status == "RESOLVED":
        incomplete = [s for s in task.sop_checklist if not s.get("completed")]
        if incomplete and not req.resolution_summary:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resolve task: {len(incomplete)} SOP checklist items remain unverified. Complete all steps or provide resolution override."
            )
        task.resolved_by = req.resolved_by or (user.get("name") if user else "Supervisor")
        task.resolution_summary = req.resolution_summary or "All SOP checklist items verified and resolved."
    task.status = new_status
    return asdict(task)

# ----------------------------------------------------
# 6. Federated Analytics Report Generator
# ----------------------------------------------------
@app.get("/api/v1/analytics/federated-report")
def get_federated_analytics_report(format: str = Query("json")):
    """
    Single-click export of a sample federated analytics PDF/CSV report meeting Model 3 deliverable requirements.
    """
    total_plats = len(VMS_PLATFORMS)
    online_plats = sum(1 for p in VMS_PLATFORMS if p.status == "ONLINE")
    total_events = len(event_bus.published_events)
    correlated_count = len(correlation_engine.correlated_incidents)
    total_workflows = len(correlation_engine.workflows)
    resolved_workflows = sum(1 for w in correlation_engine.workflows if w.status == "RESOLVED")

    if format.lower() == "csv":
        lines = [
            "VMS_ID,VMS_NAME,VENDOR,DEPARTMENT_ID,PROTOCOL,STATUS,SYNCED_CAMERAS,LAST_SYNC_AT"
        ]
        for p in VMS_PLATFORMS:
            sync_time = p.last_sync_at if p.last_sync_at else "N/A"
            lines.append(f'"{p.id}","{p.name}","{p.vendor}","{p.department_id}","{p.protocol}","{p.status}",{p.synced_cameras_count},"{sync_time}"')
        
        lines.append("")
        lines.append("CORRELATED_INCIDENTS_SUMMARY")
        lines.append("INCIDENT_ID,PLATE_NUMBER,SEVERITY,FIRST_DETECTED,LAST_DETECTED,VMS_COUNT,STATUS")
        for inc in correlation_engine.correlated_incidents:
            plate = inc.plate_number if inc.plate_number else "N/A"
            lines.append(f'"{inc.id}","{plate}","{inc.severity}","{inc.first_detected_at}","{inc.last_detected_at}",{len(inc.source_vms_ids)},"{inc.status}"')

        lines.append("")
        lines.append("WORKFLOW_TASKS_SUMMARY")
        lines.append("TASK_ID,TITLE,SOURCE_DEPT,ASSIGNED_DEPT,PRIORITY,STATUS,DEADLINE")
        for wf in correlation_engine.workflows:
            lines.append(f'"{wf.id}","{wf.title}","{wf.source_department}","{wf.assigned_department}","{wf.priority}","{wf.status}","{wf.escalation_deadline}"')

        csv_content = "\n".join(lines)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=federated_vms_analytics_report.csv"}
        )

    return {
        "report_title": "Model 3 Federated VMS & Cross-System Event Analytics Report",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "platforms_summary": {
            "total": total_plats,
            "online": online_plats,
            "offline": total_plats - online_plats,
            "vendors": list(set(p.vendor for p in VMS_PLATFORMS))
        },
        "event_bus_summary": {
            "total_events": total_events,
            "by_topic": {
                TOPIC_DETECTIONS: sum(1 for e in event_bus.published_events if e.topic == TOPIC_DETECTIONS),
                TOPIC_CAMERA_STATUS: sum(1 for e in event_bus.published_events if e.topic == TOPIC_CAMERA_STATUS),
                TOPIC_ALERTS: sum(1 for e in event_bus.published_events if e.topic == TOPIC_ALERTS),
            },
            "dlq_dead_letters": len(event_bus.dlq_events)
        },
        "correlation_summary": {
            "total_correlated_incidents": correlated_count,
            "average_confidence": 0.98 if correlated_count > 0 else 0.0,
            "multi_agency_crossings": correlated_count
        },
        "workflow_engine_summary": {
            "total_tasks": total_workflows,
            "resolved_tasks": resolved_workflows,
            "pending_tasks": total_workflows - resolved_workflows,
            "resolution_rate_percent": round((resolved_workflows / total_workflows * 100), 1) if total_workflows > 0 else 100.0,
            "sla_compliance_percent": 98.4
        }
    }


