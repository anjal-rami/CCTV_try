import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# 1. Admin Strict Password Verification
@pytest.mark.anyio
async def test_admin_login_with_correct_password_succeeds(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("mfa_required") is True or "access_token" in data

@pytest.mark.anyio
async def test_admin_login_with_incorrect_password_fails(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrongpassword999"})
    assert res.status_code == 401
    assert "invalid username or password" in res.json()["detail"].lower()

@pytest.mark.anyio
async def test_admin_login_with_other_account_password_fails(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "police123"})
    assert res.status_code == 401
    assert "invalid username or password" in res.json()["detail"].lower()

# 2. AI Analyst Strict Password Verification
@pytest.mark.anyio
async def test_analyst_login_with_correct_password_succeeds(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"username": "analyst", "password": "ai123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

@pytest.mark.anyio
async def test_analyst_login_with_wrong_password_fails(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"username": "analyst", "password": "admin123"})
    assert res.status_code == 401
    assert "invalid username or password" in res.json()["detail"].lower()

# 3. GIS, Maintenance, Tech, Viewer Wrong Password Blocks
@pytest.mark.anyio
async def test_all_roles_reject_invalid_passwords(client: AsyncClient):
    test_cases = [
        ("gis", "wrongpass"),
        ("maint", "invalidpass"),
        ("tech", "badpass"),
        ("viewer", "wrongviewerpass"),
        ("policeadmin", "arbitrary123"),
    ]
    for username, bad_pass in test_cases:
        res = await client.post("/api/v1/auth/login", json={"username": username, "password": bad_pass})
        assert res.status_code == 401, f"User {username} should be blocked with HTTP 401 for password {bad_pass}"
        assert "invalid username or password" in res.json()["detail"].lower()
