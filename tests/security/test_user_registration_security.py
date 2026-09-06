"""
Security & Governance Regression Tests for Manual User Registration Engine (POST /api/v1/auth/register).
Validates least-privilege VIEWER role assignment, input sanitization, rate limiting, honeypot protection, and password complexity.
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
async def test_registration_assigns_strictly_operator_role_pending_approval(client: AsyncClient):
    """Verify self-registration assigns strictly OPERATOR role in PENDING_APPROVAL state and blocks login until activated."""
    payload = {
        "username": "new_operator_01",
        "email": "new.operator@platform.gov.in",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "department": "Gujarat Police Department",
        "full_name": "Officer New Operator"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["role"] == "OPERATOR"
    assert data["is_active"] is False
    assert data["user_status"] == "PENDING_APPROVAL"
    assert data["username"] == "new_operator_01"

    # Verify newly registered unapproved user CANNOT log in (must return 403 Forbidden)
    login_res = await client.post("/api/v1/auth/login", json={
        "username": "new_operator_01",
        "password": "SecurePassword123!"
    })
    assert login_res.status_code == 403
    assert "pending administrative verification" in login_res.json()["detail"].lower()

@pytest.mark.anyio
async def test_registration_rejects_invalid_username_format(client: AsyncClient):
    """Username must be 4-32 characters alphanumeric with underscores/dashes."""
    invalid_usernames = [
        "usr",                 # too short (< 4 chars)
        "user@name!",          # special characters
        "user name",           # spaces not allowed
        "<script>alert(1)</script>" # script tag injection
    ]
    for invalid_un in invalid_usernames:
        payload = {
            "username": invalid_un,
            "email": "valid.email@platform.gov.in",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "department": "State Command",
            "full_name": "Test User"
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

@pytest.mark.anyio
async def test_registration_enforces_password_complexity(client: AsyncClient):
    """Password must have >=12 chars, 1 uppercase, 1 lowercase, 1 number, and 1 special char."""
    weak_passwords = [
        "Short1!",             # < 12 chars
        "lowercaseonly123!",   # no uppercase
        "UPPERCASEONLY123!",   # no lowercase
        "NoDigitsHere!",       # no digit
        "NoSpecialChar1234"    # no special char
    ]
    for weak_pwd in weak_passwords:
        payload = {
            "username": "valid_user_pwd_test",
            "email": "valid.pwd@platform.gov.in",
            "password": weak_pwd,
            "confirm_password": weak_pwd,
            "department": "State Command",
            "full_name": "Test User"
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

@pytest.mark.anyio
async def test_registration_rejects_mismatched_confirm_password(client: AsyncClient):
    """Confirm password mismatch must return 422 Unprocessable Entity."""
    payload = {
        "username": "pwd_mismatch_usr",
        "email": "mismatch@platform.gov.in",
        "password": "SecurePassword123!",
        "confirm_password": "DifferentPassword123!",
        "department": "State Command",
        "full_name": "Test Mismatch"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert "do not match" in response.json()["detail"].lower()

@pytest.mark.anyio
async def test_registration_rejects_duplicate_username_or_email(client: AsyncClient):
    """Existing username or email must return 409 Conflict."""
    payload = {
        "username": "admin", # Existing seeded user
        "email": "new.unique@platform.gov.in",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "department": "State Command",
        "full_name": "Duplicate Admin Attempt"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()

@pytest.mark.anyio
async def test_registration_honeypot_blocks_bot_attempts(client: AsyncClient):
    """If honeypot field is filled, silently discard or reject with HTTP 400 Bad Request."""
    payload = {
        "username": "bot_user_test",
        "email": "bot@platform.gov.in",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "department": "State Command",
        "full_name": "Automated Spam Bot",
        "honeypot": "http://spam-link.com"  # Bot filled this
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400

@pytest.mark.anyio
async def test_registration_rate_limiting(client: AsyncClient):
    """Enforce max 3 attempts per minute per source IP. 4th attempt returns HTTP 429."""
    for i in range(3):
        payload = {
            "username": f"rate_user_0{i}",
            "email": f"rate.user.0{i}@platform.gov.in",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "department": "State Command",
            "full_name": f"Rate User {i}"
        }
        await client.post("/api/v1/auth/register", json=payload)
    
    # 4th attempt from same IP must be rate limited (429)
    fourth_payload = {
        "username": "rate_user_exceeded",
        "email": "exceeded@platform.gov.in",
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "department": "State Command",
        "full_name": "Exceeded User"
    }
    response = await client.post("/api/v1/auth/register", json=fourth_payload)
    assert response.status_code == 429
    assert "rate limit exceeded" in response.json()["detail"].lower()
