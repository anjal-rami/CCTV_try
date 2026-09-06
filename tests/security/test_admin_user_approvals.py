"""
Automated Test Suite for Admin User Approval Workflow & Clearance Notifications.
Tests:
1. Super Admin vs Department Admin pending user listings & department boundary isolation.
2. Clearance approval and rejection with audit logging.
3. Immediate post-approval login capability (no 'pending verification' error).
4. Cross-department clearance prevention (403 Forbidden).
5. Pending counter endpoints (GET /api/v1/admin/users/pending/count and GET /api/v1/dashboard/summary).
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.seed_data import SEED_USERS
from backend.models import UserRole
from backend.auth import create_access_token

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

def get_auth_token_for(username: str):
    user = next((u for u in SEED_USERS if u.username == username or u.email == username), None)
    assert user is not None, f"User {username} not found in SEED_USERS"
    return create_access_token(user)

@pytest.mark.anyio
async def test_super_admin_fetches_all_pending_approvals(client: AsyncClient):
    token = get_auth_token_for("superadmin@platform.gov.in")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/users/pending", headers=headers)
    assert response.status_code == 200
    pending_list = response.json()
    assert len(pending_list) >= 3
    # Check required fields
    for item in pending_list:
        assert "id" in item
        assert "username" in item
        assert "email" in item
        assert "full_name" in item
        assert "employee_id" in item
        assert "department" in item
        assert "created_at" in item
        assert item["verification_status"] == "PENDING_APPROVAL" or item["user_status"] == "PENDING_APPROVAL"

@pytest.mark.anyio
async def test_department_admin_isolated_to_own_department(client: AsyncClient):
    # Police Admin (Gujarat Police Department)
    token = get_auth_token_for("policeadmin")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/users/pending", headers=headers)
    assert response.status_code == 200
    pending_list = response.json()
    assert len(pending_list) == 1
    assert pending_list[0]["id"] == "usr_pending_police"
    assert "police" in pending_list[0]["department"].lower()

@pytest.mark.anyio
async def test_unauthorized_roles_blocked_from_pending_list(client: AsyncClient):
    # Technician should receive 403 Forbidden
    tech_token = get_auth_token_for("tech")
    headers = {"Authorization": f"Bearer {tech_token}"}

    response = await client.get("/api/v1/admin/users/pending", headers=headers)
    assert response.status_code == 403

@pytest.mark.anyio
async def test_cross_department_clearance_strictly_forbidden(client: AsyncClient):
    # Police Admin attempts to approve RTO pending applicant (usr_pending_rto)
    police_token = get_auth_token_for("policeadmin")
    headers = {"Authorization": f"Bearer {police_token}"}

    payload = {"action": "APPROVE", "assigned_role": "OPERATOR"}
    response = await client.patch("/api/v1/admin/users/usr_pending_rto/clearance", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Cannot manage users from another department" in response.json()["detail"]

@pytest.mark.anyio
async def test_super_admin_approves_clearance_and_enables_instant_login(client: AsyncClient):
    super_token = get_auth_token_for("superadmin@platform.gov.in")
    headers = {"Authorization": f"Bearer {super_token}"}

    # Approve Vikram Solanki (usr_pending_transport)
    payload = {"action": "APPROVE", "assigned_role": "OPERATOR"}
    response = await client.patch("/api/v1/admin/users/usr_pending_transport/clearance", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["new_status"] == "APPROVED"

    # Verify Vikram can immediately log in without 403 pending verification error
    login_res = await client.post("/api/v1/auth/login", json={
        "username": "vikram_transport",
        "password": "VikramPass123!"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["role"] == "OPERATOR"
    assert "access_token" in login_data

    # Reset Vikram state for test reproducibility
    user = next((u for u in SEED_USERS if u.id == "usr_pending_transport"), None)
    if user:
        user.is_active = False
        user.status = "PENDING_APPROVAL"
        user.verification_status = "PENDING_APPROVAL"

@pytest.mark.anyio
async def test_admin_rejects_clearance_with_reason(client: AsyncClient):
    super_token = get_auth_token_for("superadmin@platform.gov.in")
    headers = {"Authorization": f"Bearer {super_token}"}

    # Reject usr_pending_rto
    payload = {
        "action": "REJECT",
        "rejection_reason": "Badge ID could not be verified in state personnel registry"
    }
    response = await client.patch("/api/v1/admin/users/usr_pending_rto/clearance", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["new_status"] == "REJECTED"

    # Reset for consistency
    user = next((u for u in SEED_USERS if u.id == "usr_pending_rto"), None)
    if user:
        user.is_active = False
        user.status = "PENDING_APPROVAL"
        user.verification_status = "PENDING_APPROVAL"

@pytest.mark.anyio
async def test_dashboard_summary_and_pending_counter(client: AsyncClient):
    # Public / Super Admin summary
    res = await client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["pending_count"] >= 3
    assert "total_cameras" in summary
    assert "online_cameras" in summary

    # Count endpoint
    count_res = await client.get("/api/v1/admin/users/pending/count")
    assert count_res.status_code == 200
    assert count_res.json()["pending_count"] >= 3

@pytest.mark.anyio
async def test_super_admin_fetches_approved_user_directory(client: AsyncClient):
    token = get_auth_token_for("superadmin@platform.gov.in")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/users/approved", headers=headers)
    assert response.status_code == 200
    approved_list = response.json()
    assert len(approved_list) >= 8

    # Verify field sanitization and structure
    for user in approved_list:
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "full_name" in user
        assert "employee_id" in user
        assert "department" in user
        assert "role" in user
        assert user["verification_status"] == "APPROVED"
        assert user["is_active"] is True
        # Rule 2: NEVER leak passwords or secrets
        assert "password_hash" not in user
        assert "hashed_password" not in user
        assert "password" not in user
        assert "mfa_secret" not in user

@pytest.mark.anyio
async def test_department_admin_approved_directory_isolated_to_own_department(client: AsyncClient):
    # Police Admin (Gujarat Police Department)
    token = get_auth_token_for("policeadmin")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/admin/users/approved", headers=headers)
    assert response.status_code == 200
    dept_users = response.json()
    assert len(dept_users) > 0

    # Ensure all returned users belong strictly to Gujarat Police Department
    for u in dept_users:
        assert "police" in u["department"].lower()

@pytest.mark.anyio
async def test_unauthorized_roles_blocked_from_approved_directory(client: AsyncClient):
    tech_token = get_auth_token_for("tech")
    headers = {"Authorization": f"Bearer {tech_token}"}

    response = await client.get("/api/v1/admin/users/approved", headers=headers)
    assert response.status_code == 403

@pytest.mark.anyio
async def test_clearance_approval_lifecycle_moves_user_to_approved_directory(client: AsyncClient):
    super_token = get_auth_token_for("superadmin@platform.gov.in")
    headers = {"Authorization": f"Bearer {super_token}"}

    # Verify applicant initially not in approved directory
    initial_approved = (await client.get("/api/v1/admin/users/approved", headers=headers)).json()
    assert not any(u["username"] == "ramesh_desai" for u in initial_approved)

    # Approve clearance for Ramesh Desai
    payload = {"action": "APPROVE", "assigned_role": "OPERATOR"}
    approve_res = await client.patch("/api/v1/admin/users/usr_pending_police/clearance", json=payload, headers=headers)
    assert approve_res.status_code == 200
    assert approve_res.json()["verification_status"] == "APPROVED"

    # Verify Ramesh immediately appears in approved directory
    updated_approved = (await client.get("/api/v1/admin/users/approved", headers=headers)).json()
    ramesh = next((u for u in updated_approved if u["username"] == "ramesh_desai"), None)
    assert ramesh is not None
    assert ramesh["verification_status"] == "APPROVED"
    assert ramesh["is_active"] is True
    assert ramesh["role"] == "OPERATOR"

    # Reset Ramesh state for reproducibility
    user = next((u for u in SEED_USERS if u.id == "usr_pending_police"), None)
    if user:
        user.is_active = False
        user.status = "PENDING_APPROVAL"
        user.verification_status = "PENDING_APPROVAL"

