"""
User model for SQLAlchemy ORM and user clearance management.
"""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean
from typing import Optional

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    employee_id: Mapped[str] = mapped_column(String, default="N/A")
    department: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="OPERATOR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[str] = mapped_column(String, default="PENDING_APPROVAL")
    created_at: Mapped[str] = mapped_column(String, default="2026-09-05 10:00:00")
