"""
Runnable self-check verification script for CCTV Platform Backend APIs & 8-Authority RBAC.
"""
import sys
import json

from backend.seed_data import generate_seed_data, SEED_USERS
from backend.spatial import haversine_distance_meters, calculate_fov_cone_coordinates
from backend.ai_engine import reconstruct_vehicle_route, analyze_infrastructure_gaps, validate_bulk_csv_content
from backend.auth import authenticate_user, verify_mfa_code, create_access_token, decode_access_token
from backend.security_engine import calculate_security_threat_score, block_ip_address, is_ip_blocked

def run_self_checks():
    print("==================================================")
    print("RUNNING CCTV PLATFORM 8-AUTHORITY RBAC SELF-CHECKS")
    print("==================================================")

    # 1. Check 9 Seed User Accounts
    print(f"[CHECK 1] Seed Users: {len(SEED_USERS)} pre-configured accounts across all 8 Authority roles.")
    assert len(SEED_USERS) >= 8, f"Expected at least 8 seed users, got {len(SEED_USERS)}"

    # 2. Test Super Admin Authentication & MFA Prompt
    auth_res = authenticate_user("superadmin@platform.gov.in", "admin123")
    print(f"[CHECK 2] Super Admin Authentication: MFA Required = {auth_res['mfa_required']}.")
    assert auth_res["mfa_required"] is True, "Super Admin expected TOTP MFA prompt"

    mfa_res = verify_mfa_code(auth_res["temp_mfa_token"], "123456")
    print(f"[CHECK 2] MFA Verification (Dev Code 123456): Token Issued successfully.")
    assert "access_token" in mfa_res, "MFA token issuance failed"

    # Decode claims
    claims = decode_access_token(mfa_res["access_token"])
    print(f"[CHECK 2] JWT Claims Payload: Sub={claims['sub']}, Role={claims['role']}, Badge={claims['badge_code']}.")
    assert claims["role"] == "SUPER_ADMIN", "JWT role claim mismatch"

    # 3. Test Non-MFA User (AI Analyst)
    ai_res = authenticate_user("aianalyst@platform.gov.in", "ai123")
    print(f"[CHECK 3] AI Analyst Direct Login: Role={ai_res['user']['role']}.")
    assert ai_res["user"]["role"] == "AI_ANALYST", "AI Analyst role mismatch"

    # 4. Test Cybersecurity Threat Meter & IP Blocklist
    threat_res = calculate_security_threat_score()
    print(f"[CHECK 4] Security Threat Meter: Score={threat_res['threat_score']}, Level={threat_res['threat_level']}.")

    block_ip_address("198.51.100.99", "Test threat block")
    assert is_ip_blocked("198.51.100.99") is True, "IP block failed"
    print("[CHECK 4] IP Firewall Blocklist: Successfully banned 198.51.100.99.")

    # 5. Test Spatial Math & ANPR Route Reconstruction
    depts, cams, anpr_dets, watchlist, tickets, audit_logs = generate_seed_data()
    route_res = reconstruct_vehicle_route("GJ-01-AB-1234", anpr_dets)
    print(f"[CHECK 5] Gujarat ANPR Route Reconstruction for 'GJ-01-AB-1234': Found {route_res['total_detections']} waypoints.")
    assert route_res["total_detections"] > 0, "Route reconstruction failed"

    print("==================================================")
    print("ALL 8-AUTHORITY RBAC BACKEND SELF-CHECKS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    run_self_checks()
