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
def super_admin_token():
    user = next((u for u in SEED_USERS if u.role == UserRole.SUPER_ADMIN), None)
    return create_access_token(user)

@pytest.fixture
def police_dept_admin_token():
    user = next((u for u in SEED_USERS if u.id == "usr_policeadmin"), None)
    return create_access_token(user)

@pytest.fixture
def rto_dept_admin_token():
    user = next((u for u in SEED_USERS if u.id == "usr_rtoadmin"), None)
    return create_access_token(user)

@pytest.fixture
def gis_operator_token():
    user = next((u for u in SEED_USERS if u.role == UserRole.GIS_OPERATOR), None)
    return create_access_token(user)

@pytest.fixture
def maint_officer_token():
    user = next((u for u in SEED_USERS if u.role == UserRole.MAINTENANCE_OFFICER), None)
    return create_access_token(user)

@pytest.fixture
def technician_token():
    user = next((u for u in SEED_USERS if u.role == UserRole.TECHNICIAN), None)
    return create_access_token(user)

@pytest.fixture
def ai_analyst_token():
    user = next((u for u in SEED_USERS if u.role == UserRole.AI_ANALYST), None)
    return create_access_token(user)

@pytest.fixture
def operator_token():
    user = next((u for u in SEED_USERS if u.role == UserRole.OPERATOR), None)
    return create_access_token(user)

# 1. Health Metrics Immutability Tests
@pytest.mark.anyio
async def test_human_user_cannot_mutate_health_metrics(client: AsyncClient, super_admin_token: str):
    payload = {"health_score": 100, "is_online": True, "name": "Unauthorized Health Modification"}
    res = await client.put(
        "/api/cameras/CAM-0001",
        json=payload,
        headers={"Authorization": f"Bearer {super_admin_token}"}
    )
    assert res.status_code == 403
    assert "immutable" in res.json()["detail"].lower()

@pytest.mark.anyio
async def test_internal_telemetry_daemon_can_update_health(client: AsyncClient):
    payload = {"is_online": True, "health_score": 98, "last_ping": "2026-09-05 10:00:00"}
    res = await client.post(
        "/internal/v1/telemetry/cameras/CAM-0001/health",
        json=payload,
        headers={"X-Internal-Daemon-Token": "INTERNAL-TELEMETRY-DAEMON-SECRET-KEY-2024"}
    )
    assert res.status_code == 200
    assert res.json()["health_score"] == 98

# 2. Camera Creation Authorization
@pytest.mark.anyio
async def test_unauthorized_roles_cannot_create_camera(client: AsyncClient, gis_operator_token: str, maint_officer_token: str, technician_token: str, operator_token: str):
    payload = {"name": "Unauthorized Cam", "dept_id": "DEPT-01"}
    
    for token, role_name in [(gis_operator_token, "GIS_OPERATOR"), (maint_officer_token, "MAINTENANCE_OFFICER"), (technician_token, "TECHNICIAN"), (operator_token, "OPERATOR")]:
        res = await client.post("/api/cameras", json=payload, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 403, f"{role_name} should be blocked from creating camera"

@pytest.mark.anyio
async def test_authorized_admin_can_create_camera(client: AsyncClient, super_admin_token: str):
    payload = {
        "name": "New Test Camera",
        "dept_id": "DEPT-01",
        "camera_type": "IP Bullet",
        "latitude": 23.0225,
        "longitude": 72.5714
    }
    res = await client.post("/api/cameras", json=payload, headers={"Authorization": f"Bearer {super_admin_token}"})
    assert res.status_code == 201
    assert "camera" in res.json()

# 3. GIS Operator Spatial Updates Boundary
@pytest.mark.anyio
async def test_gis_operator_can_update_spatial_fields(client: AsyncClient, gis_operator_token: str):
    spatial_payload = {
        "latitude": 23.0300,
        "longitude": 72.5800,
        "fov_azimuth": 120.0,
        "coverage_radius": 200.0
    }
    res = await client.patch("/api/cameras/CAM-0001/spatial", json=spatial_payload, headers={"Authorization": f"Bearer {gis_operator_token}"})
    assert res.status_code == 200
    assert res.json()["updated_spatial"]["latitude"] == 23.0300

@pytest.mark.anyio
async def test_gis_operator_blocked_from_editing_non_spatial_fields(client: AsyncClient, gis_operator_token: str):
    forbidden_payload = {
        "latitude": 23.0300,
        "nvr_ip": "192.168.1.100",
        "stream_url": "rtsp://malicious-stream"
    }
    res = await client.patch("/api/cameras/CAM-0001/spatial", json=forbidden_payload, headers={"Authorization": f"Bearer {gis_operator_token}"})
    assert res.status_code == 403
    assert "non-spatial fields" in res.json()["detail"].lower()

# 4. Lifecycle State Transitions
@pytest.mark.anyio
async def test_maintenance_officer_lifecycle_boundary(client: AsyncClient, maint_officer_token: str):
    # Allowed maintenance transition
    valid_res = await client.post(
        "/api/cameras/CAM-0001/lifecycle",
        json={"new_status": "Maintenance Due", "justification": "Scheduled lens cleaning ticket #102"},
        headers={"Authorization": f"Bearer {maint_officer_token}"}
    )
    assert valid_res.status_code == 200

    # Forbidden administrative transition (e.g. Decommissioned)
    invalid_res = await client.post(
        "/api/cameras/CAM-0001/lifecycle",
        json={"new_status": "Decommissioned", "justification": "Asset end of life"},
        headers={"Authorization": f"Bearer {maint_officer_token}"}
    )
    assert invalid_res.status_code == 403

# 5. Row-Level Security (RLS) Cross-Department Scoping
@pytest.mark.anyio
async def test_department_admin_cannot_delete_other_dept_camera(client: AsyncClient, rto_dept_admin_token: str):
    # Police camera CAM-0001 (DEPT-01)
    res = await client.delete("/api/cameras/CAM-0001", headers={"Authorization": f"Bearer {rto_dept_admin_token}"})
    assert res.status_code == 403

# 6. Sensitive Stream Credentials Access
@pytest.mark.anyio
async def test_sensitive_credentials_boundary(client: AsyncClient, super_admin_token: str, gis_operator_token: str, technician_token: str, operator_token: str):
    admin_res = await client.get("/api/cameras/CAM-0001/credentials", headers={"Authorization": f"Bearer {super_admin_token}"})
    assert admin_res.status_code == 200
    assert "decryption_key" in admin_res.json()

    for token, role_name in [(gis_operator_token, "GIS_OPERATOR"), (technician_token, "TECHNICIAN"), (operator_token, "OPERATOR")]:
        unauth_res = await client.get("/api/cameras/CAM-0001/credentials", headers={"Authorization": f"Bearer {token}"})
        assert unauth_res.status_code == 403, f"{role_name} should be blocked from reading credentials"
