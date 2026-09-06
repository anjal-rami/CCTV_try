import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def http_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if data and isinstance(data, dict):
        data_bytes = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    elif data and isinstance(data, str):
        data_bytes = data.encode("utf-8")
    else:
        data_bytes = None

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"detail": body}
        return e.code, parsed

def run_security_audit():
    log("==========================================================================")
    log("EXHAUSTIVE SECURITY AUDIT & PRIVILEGE ESCALATION FIX VERIFICATION")
    log("==========================================================================")

    # 1. Fetch seed users and get access tokens
    log("1. Authenticating all 9 seed accounts across 8 Authorities...")
    tokens = {}
    users_info = {}

    seed_resp_status, seed_users = http_request(f"{BASE_URL}/api/v1/auth/seed-users")
    assert seed_resp_status == 200, "Failed to fetch seed users"

    for u in seed_users:
        email = u["email"]
        role = u["role"]
        # Login
        status_code, login_res = http_request(
            f"{BASE_URL}/api/v1/auth/login",
            method="POST",
            data={"email": email, "password": u["password_hint"]}
        )
        if login_res.get("mfa_required"):
            # Verify MFA
            status_code, mfa_res = http_request(
                f"{BASE_URL}/api/v1/auth/verify-mfa",
                method="POST",
                data={"temp_token": login_res["temp_mfa_token"], "totp_code": "123456"}
            )
            tokens[role] = mfa_res["access_token"]
            users_info[role] = mfa_res["user"]
        else:
            tokens[role] = login_res["access_token"]
            users_info[role] = login_res["user"]

    log(f"   Successfully obtained JWT tokens for roles: {list(tokens.keys())}")

    # 2. Test Watchlist Mutation Lockdown (CRITICAL ROOT CAUSE FIX)
    log("\n2. Testing Watchlist Mutation Security Patch (POST /api/v1/watchlist)...")
    
    # Authorized Roles: SUPER_ADMIN, AI_ANALYST, Police DEPARTMENT_ADMIN
    auth_roles_for_watchlist = ["SUPER_ADMIN", "AI_ANALYST"]
<<<<<<< HEAD
    unauth_roles_for_watchlist = ["TECHNICIAN", "MAINTENANCE_OFFICER", "SECURITY_ADMIN", "GIS_OPERATOR", "OPERATOR"]
=======
    unauth_roles_for_watchlist = ["TECHNICIAN", "MAINTENANCE_OFFICER", "SECURITY_ADMIN", "GIS_OPERATOR", "VIEWER"]
>>>>>>> 8ba9ff981a3a31412079589b7b323d6b617498da

    # Test Authorized Watchlist Addition
    super_admin_hdr = {"Authorization": f"Bearer {tokens['SUPER_ADMIN']}"}
    st, res = http_request(
        f"{BASE_URL}/api/v1/watchlist",
        method="POST",
        data={"plate_number": "GJ-01-SEC-9999", "category": "Stolen SUV", "description": "Audit Test Plate", "severity": "Critical"},
        headers=super_admin_hdr
    )
    assert st in (200, 201), f"SUPER_ADMIN failed to add watchlist item: {res}"
    log("   [PASSED] SUPER_ADMIN successfully created Watchlist entry.")

    # Test Unauthorized Watchlist Addition (e.g. TECHNICIAN, SECURITY_ADMIN, VIEWER)
    for unauth_role in unauth_roles_for_watchlist:
        hdr = {"Authorization": f"Bearer {tokens[unauth_role]}"}
        st, res = http_request(
            f"{BASE_URL}/api/v1/watchlist",
            method="POST",
            data={"plate_number": "GJ-99-ILLEGAL-01", "category": "Unauthorized Mutation"},
            headers=hdr
        )
        assert st == 403, f"Privilege Escalation Vulnerability! Role {unauth_role} was able to mutate watchlist! Status: {st}"
        log(f"   [PASSED] {unauth_role} Watchlist Mutation blocked with HTTP 403 Forbidden.")

    # 3. Verify Security Incident Log for Watchlist Mutation Block
    log("\n3. Verifying Security Audit Log generated for WATCHLIST_MUTATION_DENIED...")
    sec_hdr = {"Authorization": f"Bearer {tokens['SECURITY_ADMIN']}"}
    st, incidents = http_request(f"{BASE_URL}/api/v1/security/incidents", headers=sec_hdr)
    assert st == 200, "Failed to read security incidents"
    denied_incidents = [i for i in incidents if i.get("threat_type") == "WATCHLIST_MUTATION_DENIED"]
    assert len(denied_incidents) > 0, "No WATCHLIST_MUTATION_DENIED incident found in Security Log!"
    log(f"   [PASSED] Found {len(denied_incidents)} Security Audit Incidents for unauthorized Watchlist mutation attempts.")

    # 4. Technician Endpoint Lockdown Audit
    log("\n4. Auditing Technician Endpoint Boundaries...")
    tech_hdr = {"Authorization": f"Bearer {tokens['TECHNICIAN']}"}

    # Allowed for Technician: GET /api/v1/technician/tasks
    st, tasks = http_request(f"{BASE_URL}/api/v1/technician/tasks", headers=tech_hdr)
    assert st == 200, "Technician failed to fetch assigned tasks"
    log("   [PASSED] TECHNICIAN can access assigned tasks.")

    # Blocked for Technician: Camera Registry
    st, _ = http_request(f"{BASE_URL}/api/cameras", headers=tech_hdr)
    assert st == 403, "Technician accessed overall camera registry!"
    log("   [PASSED] TECHNICIAN blocked from overall camera registry (HTTP 403).")

    # Blocked for Technician: GIS Cameras
    st, _ = http_request(f"{BASE_URL}/api/gis/cameras", headers=tech_hdr)
    assert st == 403, "Technician accessed GIS spatial feeds!"
    log("   [PASSED] TECHNICIAN blocked from GIS map layers (HTTP 403).")

    # Blocked for Technician: Security Forensics
    st, _ = http_request(f"{BASE_URL}/api/v1/security/threat-meter", headers=tech_hdr)
    assert st == 403, "Technician accessed Security Threat Meter!"
    log("   [PASSED] TECHNICIAN blocked from Security Threat Meter (HTTP 403).")

    # 5. Security Admin Boundaries Audit
    log("\n5. Auditing Security Admin Boundaries...")
    st, _ = http_request(f"{BASE_URL}/api/v1/security/threat-meter", headers=sec_hdr)
    assert st == 200, "Security Admin failed to access Security Threat Meter"
    log("   [PASSED] SECURITY_ADMIN has full access to Security Threat Meter.")

    log("\n==========================================================================")
    log("ALL PRIVILEGE ESCALATION SECURITY AUDIT CHECKS PASSED CLEANLY!")
    log("==========================================================================")

if __name__ == "__main__":
    run_security_audit()
