import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.auth import create_access_token
from backend.seed_data import SEED_USERS
from backend.models import UserRole

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def technician_token():
    tech_user = next((u for u in SEED_USERS if u.role == UserRole.TECHNICIAN), None)
    return create_access_token(tech_user)

@pytest.fixture
def maintenance_officer_token():
    maint_user = next((u for u in SEED_USERS if u.role == UserRole.MAINTENANCE_OFFICER), None)
    return create_access_token(maint_user)

@pytest.fixture
def ai_analyst_token():
    ai_user = next((u for u in SEED_USERS if u.role == UserRole.AI_ANALYST), None)
    return create_access_token(ai_user)

@pytest.mark.anyio
async def test_amc_technician_cannot_access_route_tracker(client: AsyncClient, technician_token: str):
    response = await client.get(
        "/api/v1/tracking/route/GJ01AB1234",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert response.status_code == 403
    assert "detail" in response.json()

@pytest.mark.anyio
async def test_maintenance_officer_cannot_search_anpr_routes(client: AsyncClient, maintenance_officer_token: str):
    response = await client.get(
        "/api/v1/tracking/vehicle-movements?plate=GJ01AB1234",
        headers={"Authorization": f"Bearer {maintenance_officer_token}"}
    )
    assert response.status_code == 403

@pytest.mark.anyio
async def test_ai_analyst_can_access_route_tracker(client: AsyncClient, ai_analyst_token: str):
    response = await client.get(
        "/api/v1/tracking/route/GJ01AB1234",
        headers={"Authorization": f"Bearer {ai_analyst_token}"}
    )
    assert response.status_code == 200
