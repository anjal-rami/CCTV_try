"""
Async Database Session & Engine setup for User Clearance Workflow.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from app.models.user import Base, User
from app.models.audit import SecurityAuditLog
from backend.seed_data import SEED_USERS

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

_initialized = False

async def init_db():
    global _initialized
    if _initialized:
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for u in SEED_USERS:
            orm_user = User(
                id=str(u.id),
                username=u.username,
                email=u.email,
                full_name=getattr(u, "full_name", u.name),
                employee_id=getattr(u, "employee_id", u.badge_code),
                department=getattr(u, "department", u.department_name or ""),
                role=u.role.value if hasattr(u.role, "value") else str(u.role),
                is_active=u.is_active,
                verification_status=getattr(u, "verification_status", u.status),
                created_at=getattr(u, "created_at", "2026-09-05 10:00:00")
            )
            session.add(orm_user)
        await session.commit()
    _initialized = True

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    await init_db()
    async with AsyncSessionLocal() as session:
        yield session
