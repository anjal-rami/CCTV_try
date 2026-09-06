"""
SecurityAuditLog SQLAlchemy model.
"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from typing import Optional
from datetime import datetime, timezone
from .user import Base

class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String)
    actor_username: Mapped[str] = mapped_column(String)
    details: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
