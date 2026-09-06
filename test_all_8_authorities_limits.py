import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def http_req(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    if data and isinstance(data, dict):
        data_bytes = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
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

def verify_all_authorities_limits():
    log("==========================================================================")
    log("EXHAUSTIVE 8-AUTHORITY AUTHORIZATION LIMIT VERIFICATION MATRIX")
    log("==========================================================================")

    # 1. Obtain JWT tokens for all seed users
    log("1. Authenticating accounts for all 8 Authorities...")
    tokens = {}
    st, seed_users = http_req(f"{BASE_URL}/api/v1/auth/seed-users")
    assert st == 200, "Failed to get seed users"

    for u in seed_users:
        email = u["email"]
        role = u["role"]
        dept = u.get("department_name", "")
        key = f"{role}_{u['id']}"

        st, login_res = http_req(f"{BASE_URL}/api/v1/auth/login", method="POST", data={"email": email, "password": u["password_hint"]})
        if login_res.get("mfa_required"):
            st, mfa_res = http_req(f"{BASE_URL}/api/v1/auth/verify-mfa", method="POST", data={"temp_token": login_res["temp_mfa_token"], "totp_code": "123456"})
            token = mfa_res["access_token"]
        else:
            token = login_res["access_token"]
        
        tokens[key] = {"token": token, "role": role, "email": email, "name": u["name"], "dept": dept}

    log(f"   Tokens generated for {len(tokens)} accounts across all 8 Authorities.\n")

    # Helper for testing endpoints with expects
    def test_endpoint(role_key, method, path, payload, expected_status, test_label):
        info = tokens[role_key]
        hdr = {"Authorization": f"Bearer {info['token']}"}
        st, res = http_req(f"{BASE_URL}{path}", method=method, data=payload, headers=hdr)
        pass_check = (st == expected_status)
        symbol = "PASSED" if pass_check else "FAILED"
        log(f"   [{symbol}] [{info['role']}] {test_label} -> Got HTTP {st} (Expected {expected_status})")
        assert pass_check, f"Boundary Violation! {info['role']} on {path} returned {st} instead of {expected_status}. Details: {res}"

    # --------------------------------------------------------------------------
    # AUTHORITY 1: SUPER_ADMIN
    # --------------------------------------------------------------------------
    log("2. Verifying SUPER_ADMIN Limits (Full Control across all modules)...")
    admin_key = next(k for k in tokens if "SUPER_ADMIN" in k)
    test_endpoint(admin_key, "GET", "/api/v1/security/threat-meter", None, 200, "Access Security Threat Meter")
    test_endpoint(admin_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01SA1001", "reason": "Statewide Alert"}, 201, "Create Watchlist Item")
    test_endpoint(admin_key, "GET", "/api/cameras", None, 200, "Query Camera Registry")

    # --------------------------------------------------------------------------
    # AUTHORITY 2: SECURITY_ADMIN
    # --------------------------------------------------------------------------
    log("\n3. Verifying SECURITY_ADMIN Limits (Security Command Only, Blocked from Police Watchlists & Cameras)...")
    sec_key = next(k for k in tokens if "SECURITY_ADMIN" in k)
    test_endpoint(sec_key, "GET", "/api/v1/security/threat-meter", None, 200, "Access Security Threat Meter")
    test_endpoint(sec_key, "GET", "/api/v1/security/incidents", None, 200, "Read Audit Log Incidents")
    test_endpoint(sec_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01SEC001"}, 403, "BLOCKED: Watchlist Mutation")
    test_endpoint(sec_key, "GET", "/api/anpr/search?plate_number=GJ01", None, 403, "BLOCKED: ANPR Plate Search")

    # --------------------------------------------------------------------------
    # AUTHORITY 3: DEPARTMENT_ADMIN (Police vs Civil)
    # --------------------------------------------------------------------------
    log("\n4. Verifying DEPARTMENT_ADMIN Limits (Scoped Dept Access, Law Enforcement vs Civil)...")
    police_key = next(k for k in tokens if "usr_policeadmin" in k)
    test_endpoint(police_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01POL999", "reason": "Police FIR"}, 201, "Police Dept Admin Watchlist Mutation")
    test_endpoint(police_key, "GET", "/api/v1/security/threat-meter", None, 403, "BLOCKED: Security Threat Meter")

    rto_key = next(k for k in tokens if "usr_rtoadmin" in k)
    test_endpoint(rto_key, "GET", "/api/cameras", None, 200, "RTO Dept Cameras Query")
    test_endpoint(rto_key, "GET", "/api/v1/security/threat-meter", None, 403, "BLOCKED: Security Threat Meter")

    # --------------------------------------------------------------------------
    # AUTHORITY 4: AI_ANALYST
    # --------------------------------------------------------------------------
    log("\n5. Verifying AI_ANALYST Limits (ANPR & Route Tracking Allowed, Security Forensics Blocked)...")
    ai_key = next(k for k in tokens if "AI_ANALYST" in k)
    test_endpoint(ai_key, "GET", "/api/anpr/search?plate_number=GJ-01-AB-1234", None, 200, "ANPR Search & Route Reconstruction")
    test_endpoint(ai_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01AI7777", "reason": "AI YOLO Detection"}, 201, "Watchlist Addition")
    test_endpoint(ai_key, "GET", "/api/v1/security/threat-meter", None, 403, "BLOCKED: Security Threat Meter")

    # --------------------------------------------------------------------------
    # AUTHORITY 5: GIS_OPERATOR
    # --------------------------------------------------------------------------
    log("\n6. Verifying GIS_OPERATOR Limits (Spatial Map Allowed, ANPR & Watchlist Blocked)...")
    gis_key = next(k for k in tokens if "GIS_OPERATOR" in k)
    test_endpoint(gis_key, "GET", "/api/gis/cameras", None, 200, "GIS Map & FOV Coordinates")
    test_endpoint(gis_key, "GET", "/api/anpr/search?plate_number=GJ01", None, 403, "BLOCKED: ANPR Search")
    test_endpoint(gis_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01GIS000"}, 403, "BLOCKED: Watchlist Mutation")
    test_endpoint(gis_key, "GET", "/api/v1/security/threat-meter", None, 403, "BLOCKED: Security Threat Meter")

    # --------------------------------------------------------------------------
    # AUTHORITY 6: MAINTENANCE_OFFICER
    # --------------------------------------------------------------------------
    log("\n7. Verifying MAINTENANCE_OFFICER Limits (Tickets Allowed, Surveillance & ANPR Blocked)...")
    maint_key = next(k for k in tokens if "MAINTENANCE_OFFICER" in k)
    test_endpoint(maint_key, "GET", "/api/tickets", None, 200, "Fetch Maintenance Tickets")
    test_endpoint(maint_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01MNT000"}, 403, "BLOCKED: Watchlist Mutation")
    test_endpoint(maint_key, "GET", "/api/stream/CAM-0001", None, 200, "Fetch Maintenance Stream Spec")

    # --------------------------------------------------------------------------
    # AUTHORITY 7: TECHNICIAN
    # --------------------------------------------------------------------------
    log("\n8. Verifying TECHNICIAN Limits (Strictly Assigned Tasks Only)...")
    tech_key = next(k for k in tokens if "TECHNICIAN" in k)
    test_endpoint(tech_key, "GET", "/api/v1/technician/tasks", None, 200, "View Personal Assigned Work Orders")
    test_endpoint(tech_key, "GET", "/api/cameras", None, 403, "BLOCKED: Camera Registry Search")
    test_endpoint(tech_key, "GET", "/api/gis/cameras", None, 403, "BLOCKED: GIS Map Spatial Cones")
    test_endpoint(tech_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01TECH00"}, 403, "BLOCKED: Watchlist Mutation")
    test_endpoint(tech_key, "GET", "/api/stream/CAM-0001", None, 403, "BLOCKED: Surveillance Stream Access")
    test_endpoint(tech_key, "GET", "/api/v1/security/threat-meter", None, 403, "BLOCKED: Security Threat Meter")

    # --------------------------------------------------------------------------
    # AUTHORITY 8: VIEWER
    # --------------------------------------------------------------------------
    log("\n9. Verifying VIEWER Limits (Masked Monitoring Only, AI/ANPR/Watchlist/Tickets Blocked)...")
    viewer_key = next(k for k in tokens if "VIEWER" in k)
    test_endpoint(viewer_key, "GET", "/api/anpr/search?plate_number=GJ01", None, 403, "BLOCKED: ANPR Search")
    test_endpoint(viewer_key, "POST", "/api/v1/watchlist", {"license_plate": "GJ01VIEW00"}, 403, "BLOCKED: Watchlist Mutation")
    test_endpoint(viewer_key, "GET", "/api/gap-analysis", None, 403, "BLOCKED: Gap Analysis Metrics")
    test_endpoint(viewer_key, "GET", "/api/v1/security/threat-meter", None, 403, "BLOCKED: Security Threat Meter")

    log("\n==========================================================================")
    log("ALL 8 AUTHORITIES ARE CONFIRMED OPERATING STRICTLY WITHIN AUTHORIZATION LIMITS!")
    log("==========================================================================")

if __name__ == "__main__":
    verify_all_authorities_limits()
