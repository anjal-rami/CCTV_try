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
def maint_officer_token():
    maint_user = next((u for u in SEED_USERS if u.role == UserRole.MAINTENANCE_OFFICER), None)
    return create_access_token(maint_user)

@pytest.fixture
def operator_token():
    operator_user = next((u for u in SEED_USERS if u.role == UserRole.OPERATOR), None)
    return create_access_token(operator_user)

@pytest.fixture
def ai_analyst_token():
    ai_user = next((u for u in SEED_USERS if u.role == UserRole.AI_ANALYST), None)
    return create_access_token(ai_user)

@pytest.fixture
def police_dept_admin_token():
    police_user = next((u for u in SEED_USERS if u.id == "usr_policeadmin"), None)
    return create_access_token(police_user)

@pytest.mark.anyio
async def test_technician_cannot_create_watchlist_entry(client: AsyncClient, technician_token: str):
    payload = {
        "license_plate": "GJ01AB1234",
        "reason": "Stolen vehicle suspicion",
        "severity": "CRITICAL"
    }
    response = await client.post(
        "/api/v1/watchlist",
        json=payload,
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert response.status_code == 403
    assert "detail" in response.json()

@pytest.mark.anyio
async def test_operator_cannot_access_anpr_or_route_tracker(client: AsyncClient, operator_token: str):
    anpr_res = await client.get(
        "/api/v1/ai/anpr/search?plate=GJ01",
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert anpr_res.status_code == 403

    route_res = await client.get(
        "/api/v1/tracking/route/GJ01AB1234",
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert route_res.status_code == 403

@pytest.mark.anyio
async def test_technician_cannot_access_route_tracking_endpoints(client: AsyncClient, technician_token: str):
    route_res = await client.get(
        "/api/v1/tracking/route/GJ01AB1234",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert route_res.status_code == 403

    movements_res = await client.get(
        "/api/v1/tracking/vehicle-movements?plate=GJ01AB1234",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert movements_res.status_code == 403

    trajectory_res = await client.get(
        "/api/v1/ai/anpr/trajectory?plate=GJ01AB1234",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert trajectory_res.status_code == 403

    stream_res = await client.get(
        "/api/v1/tracking/live-stream/GJ01AB1234",
        headers={"Authorization": f"Bearer {technician_token}"}
    )
    assert stream_res.status_code == 403

@pytest.mark.anyio
async def test_maintenance_officer_cannot_access_route_tracking(client: AsyncClient, maint_officer_token: str):
    response = await client.get(
        "/api/v1/tracking/route/GJ01AB1234",
        headers={"Authorization": f"Bearer {maint_officer_token}"}
    )
    assert response.status_code == 403

@pytest.mark.anyio
async def test_authorized_analyst_can_create_watchlist(client: AsyncClient, ai_analyst_token: str):
    payload = {
        "license_plate": "GJ05CD5678",
        "reason": "Wanted suspect vehicle",
        "severity": "HIGH"
    }
    response = await client.post(
        "/api/v1/watchlist",
        json=payload,
        headers={"Authorization": f"Bearer {ai_analyst_token}"}
    )
    assert response.status_code == 201

@pytest.mark.anyio
async def test_authorized_law_enforcement_can_access_route_tracking(client: AsyncClient, ai_analyst_token: str, police_dept_admin_token: str):
    analyst_res = await client.get(
        "/api/v1/tracking/route/GJ01AB1234",
        headers={"Authorization": f"Bearer {ai_analyst_token}"}
    )
    assert analyst_res.status_code == 200

    police_res = await client.get(
        "/api/v1/tracking/route/GJ01AB1234",
        headers={"Authorization": f"Bearer {police_dept_admin_token}"}
    )
    assert police_res.status_code == 200
