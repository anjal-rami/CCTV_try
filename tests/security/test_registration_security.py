"""
Security Integration Tests for User Registration Engine safeguards.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.auth import REGISTRATION_ATTEMPTS

@pytest.fixture
async def client():
    REGISTRATION_ATTEMPTS.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    REGISTRATION_ATTEMPTS.clear()

@pytest.mark.anyio
async def test_registration_prevents_privilege_escalation(client: AsyncClient):
    # Attempt to inject SUPER_ADMIN role in registration payload
    malicious_payload = {
        "username": "attacker_user",
        "email": "attacker@gov.in",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "department": "Gujarat Police Department",
        "full_name": "Attacker Test",
        "role": "SUPER_ADMIN"  # Malicious injection
    }
    response = await client.post("/api/v1/auth/register", json=malicious_payload)
    assert response.status_code == 201
    
    # Verify the backend assigned OPERATOR despite the injected payload
    data = response.json()
    assert data["role"] == "OPERATOR"

@pytest.mark.anyio
async def test_registration_rejects_weak_passwords(client: AsyncClient):
    weak_payload = {
        "username": "new_user_1",
        "email": "user1@gov.in",
        "password": "weakpassword",
        "confirm_password": "weakpassword",
        "department": "Gujarat State Transport Corp (GSRTC)",
        "full_name": "User One"
    }
    response = await client.post("/api/v1/auth/register", json=weak_payload)
    assert response.status_code in [400, 422]

@pytest.mark.anyio
async def test_registration_honeypot_blocks_bots(client: AsyncClient):
    bot_payload = {
        "username": "bot_user_99",
        "email": "bot@spam.com",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "department": "Health & Family Welfare Dept Gujarat",
        "full_name": "Bot Automation",
        "honeypot": "spam_value"
    }
    response = await client.post("/api/v1/auth/register", json=bot_payload)
    assert response.status_code == 400
