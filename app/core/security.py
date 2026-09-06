"""
Core security dependencies and authentication helpers.
"""
from fastapi import Depends, HTTPException, Header, status
from typing import Optional, Dict, Any
from app.models.user import User
from backend.auth import decode_access_token
from backend.seed_data import SEED_USERS

async def get_current_active_user(
    authorization: Optional[str] = Header(None)
) -> User:
    if not authorization:
        # Fallback for dev/unauthenticated testing if needed, but raise 401 standard
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required."
        )

    try:
        token = authorization.replace("Bearer ", "").strip()
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )

    sub = payload.get("sub")
    username = payload.get("username")
    role = payload.get("role", "OPERATOR")
    dept = payload.get("department_name") or payload.get("department") or ""

    user = User(
        id=str(sub) if sub else "usr_current",
        username=username or "admin",
        email=payload.get("email", "admin@platform.gov.in"),
        full_name=payload.get("name", "Command Administrator"),
        employee_id=payload.get("badge_code", "GJ-001"),
        department=dept,
        role=role,
        is_active=True,
        verification_status="APPROVED"
    )
    return user
