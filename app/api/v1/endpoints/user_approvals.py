from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User
from app.models.audit import SecurityAuditLog
from app.core.security import get_current_active_user

router = APIRouter(prefix="/api/v1/admin/users", tags=["User Approvals"])

class ApprovedUserOut(BaseModel):
    id: Union[int, str]
    username: str
    email: str
    full_name: str
    employee_id: Optional[str] = "N/A"
    department: str
    role: str
    verification_status: str
    is_active: bool
    created_at: Optional[Union[datetime, str]] = None
    approved_at: Optional[Union[datetime, str]] = None

    class Config:
        from_attributes = True
class ApprovalActionRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    assigned_role: str = "OPERATOR"  # Can elevate if necessary
    rejection_reason: Optional[str] = None

# 1. Fetch Pending Approvals List
@router.get("/pending")
async def get_pending_registrations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["SUPER_ADMIN", "DEPARTMENT_ADMIN"]:
        raise HTTPException(status_code=403, detail="Unauthorized access.")

    query = select(User).where(User.verification_status == "PENDING_APPROVAL")
    
    # Department Admin can only review registrations for their department
    if current_user.role == "DEPARTMENT_ADMIN":
        query = query.where(User.department == current_user.department)

    result = await db.execute(query)
    pending_users = result.scalars().all()
    
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "employee_id": getattr(u, "employee_id", "N/A"),
            "department": u.department,
            "created_at": u.created_at,
            "verification_status": u.verification_status,
            "user_status": u.verification_status
        }
        for u in pending_users
    ]

# 2. Fetch Pending Count
@router.get("/pending/count")
async def get_pending_registrations_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["SUPER_ADMIN", "DEPARTMENT_ADMIN"]:
        raise HTTPException(status_code=403, detail="Unauthorized access.")

    query = select(User).where(User.verification_status == "PENDING_APPROVAL")
    if current_user.role == "DEPARTMENT_ADMIN":
        query = query.where(User.department == current_user.department)

    result = await db.execute(query)
    count = len(result.scalars().all())
    return {"pending_count": count}

# 3. Fetch Approved Active Personnel Directory
@router.get("/approved", response_model=List[ApprovedUserOut])
async def get_approved_users(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Rule 1 & Rule 4: Access Control & Multi-Tenant Boundaries
    if current_user.role not in ["SUPER_ADMIN", "DEPARTMENT_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Super Admins and Department Admins."
        )

    # Base query: Only retrieve approved and active government users
    query = select(User).where(
        (User.verification_status == "APPROVED") & (User.is_active == True)
    )

    # Department Admins can only view approved users inside their assigned department
    if current_user.role == "DEPARTMENT_ADMIN":
        query = query.where(User.department == current_user.department)

    result = await db.execute(query)
    approved_users = result.scalars().all()

    # Rule 2: NEVER leak hashed_password or sensitive auth tokens in return payload
    return [
        ApprovedUserOut(
            id=u.id,
            username=u.username or u.email.split("@")[0],
            email=u.email,
            full_name=u.full_name or "N/A",
            employee_id=getattr(u, "employee_id", "N/A") or "N/A",
            department=u.department or "N/A",
            role=u.role,
            verification_status=u.verification_status,
            is_active=u.is_active,
            created_at=getattr(u, "created_at", None),
            approved_at=getattr(u, "updated_at", None)
        )
        for u in approved_users
    ]
# 3. Approve or Reject Account
@router.patch("/{user_id}/clearance")
async def process_user_clearance(
    user_id: Any,
    payload: ApprovalActionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in ["SUPER_ADMIN", "DEPARTMENT_ADMIN"]:
        raise HTTPException(status_code=403, detail="Unauthorized access.")

    user = await db.get(User, str(user_id))
    if not user:
        res = await db.execute(select(User).where((User.id == str(user_id)) | (User.username == str(user_id))))
        user = res.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if current_user.role == "DEPARTMENT_ADMIN" and user.department != current_user.department:
        raise HTTPException(status_code=403, detail="Cannot manage users from another department.")

    action_upper = payload.action.upper()
    if action_upper == "APPROVE":
        user.is_active = True
        user.verification_status = "APPROVED"
        user.role = payload.assigned_role
        audit_action = "USER_REGISTRATION_APPROVED"
        details = f"Approved by {current_user.username} as {user.role}"
    elif action_upper == "REJECT":
        user.is_active = False
        user.verification_status = "REJECTED"
        audit_action = "USER_REGISTRATION_REJECTED"
        details = f"Rejected by {current_user.username}. Reason: {payload.rejection_reason or 'Credentials rejected'}"
    else:
        raise HTTPException(status_code=400, detail="Invalid action.")

    db.add(SecurityAuditLog(
        action=audit_action,
        actor_username=current_user.username,
        details=details
    ))
    await db.commit()

    # Sync back with SEED_USERS and AUDIT_LOGS in backend
    try:
        from backend.seed_data import SEED_USERS
        from backend.models import UserRole, AuditLog
        from backend.main import AUDIT_LOGS
        from datetime import datetime, timezone

        target = next((su for su in SEED_USERS if str(su.id) == str(user.id) or su.username == user.username), None)
        if target:
            target.is_active = user.is_active
            target.status = user.verification_status
            target.verification_status = user.verification_status
            if action_upper == "APPROVE":
                try:
                    target.role = UserRole(payload.assigned_role)
                except Exception:
                    target.role = UserRole.OPERATOR
                target.role_title = payload.assigned_role.replace("_", " ").title()

        AUDIT_LOGS.append(AuditLog(
            id=f"AUD-{len(AUDIT_LOGS)+1:04d}",
            camera_id=None,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            user_id=current_user.id,
            user_name=current_user.full_name or current_user.username,
            role=current_user.role,
            action_type=audit_action,
            previous_state="PENDING_APPROVAL",
            new_state=user.verification_status,
            justification=details,
            client_ip="127.0.0.1"
        ))
    except Exception:
        pass

    return {"status": "success", "user_id": user.id, "new_status": user.verification_status, "verification_status": user.verification_status}
