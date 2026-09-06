import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.anyio
async def test_admin_login_fails_with_wrong_password(client: AsyncClient):
    # Attempting to log into admin with an invalid password
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "WrongPassword123!"}
    )
    # MUST return 401 Unauthorized, never 200 OK
    assert response.status_code == 401
    assert "access_token" not in response.json()

@pytest.mark.anyio
async def test_admin_login_succeeds_with_correct_password(client: AsyncClient):
    # Attempting login with the correct seeded password
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "Admin@Secure2026!"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
