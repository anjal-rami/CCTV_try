"""
Realistic seed data generator for 26 Government Departments of Gujarat, 500+ Camera Nodes,
ANPR Detection Logs, Watchlists, Maintenance Tickets, and Audit Trails.
"""
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple
from .models import Department, Camera, AnprDetection, WatchlistItem, MaintenanceTicket, AuditLog, User, UserRole, VMSPlatform

SEED_VMS_PLATFORMS: List[VMSPlatform] = [
    VMSPlatform(
        id="VMS-POLICE-01",
        name="Gujarat Police Central Milestone VMS",
        department_id="DEPT-01",
        vendor="Milestone",
        version="XProtect 2024 R1",
        protocol="REST API",
        base_endpoint_url="http://127.0.0.1:8081",
        credential_secret_ref="vault://vms/police/admin_cred",
        adapter_type="milestone",
        status="ONLINE",
        created_at="2026-09-01 10:00:00",
        last_sync_at="2026-09-05 14:00:00",
        synced_cameras_count=2
    ),
    VMSPlatform(
        id="VMS-MUNICIPAL-01",
        name="Municipal Civic Centers Hikvision Cluster",
        department_id="DEPT-04",
        vendor="Hikvision",
        version="ISAPI v2.6",
        protocol="REST/ISAPI",
        base_endpoint_url="http://127.0.0.1:8082",
        credential_secret_ref="vault://vms/municipal/isapi_digest",
        adapter_type="hikvision_isapi",
        status="ONLINE",
        created_at="2026-09-02 11:30:00",
        last_sync_at="2026-09-05 14:05:00",
        synced_cameras_count=2
    ),
    VMSPlatform(
        id="VMS-TRANSIT-01",
        name="GSRTC Highway Transit Axis Guardian",
        department_id="DEPT-02",
        vendor="Axis",
        version="Camera Station Pro 6.1",
        protocol="ONVIF/RTSP",
        base_endpoint_url="rtsp://axis-gsrtc.transit.local:554",
        credential_secret_ref="vault://vms/gsrtc/onvif_wssec",
        adapter_type="generic_onvif",
        status="ONLINE",
        created_at="2026-09-03 09:15:00",
        last_sync_at="2026-09-05 13:45:00",
        synced_cameras_count=1
    )
]

SEED_USERS: List[User] = [
    User(
        id="usr_superadmin",
        name="Comm. Rajesh Patel",
        email="superadmin@platform.gov.in",
        username="admin",
        password_hash="admin123",
        role=UserRole.SUPER_ADMIN,
        role_title="State Command Director General",
        department_id=None,
        department_name="All 26 Sovereign Departments",
        badge_code="GJ-HQ-001",
        mfa_enabled=True
    ),
    User(
        id="usr_securityadmin",
        name="Officer Vikram Solanki",
        email="securityadmin@platform.gov.in",
        username="secadmin",
        password_hash="sec123",
        role=UserRole.SECURITY_ADMIN,
        role_title="Cybersecurity & Compliance Director",
        department_id=None,
        department_name="State Cyber Defense Unit",
        badge_code="GJ-SEC-007",
        mfa_enabled=True
    ),
    User(
        id="usr_policeadmin",
        name="Supt. Anita Shah",
        email="policeadmin@platform.gov.in",
        username="policeadmin",
        password_hash="police123",
        role=UserRole.DEPARTMENT_ADMIN,
        role_title="Police Department Head",
        department_id="DEPT-01",
        department_name="Gujarat Police Department",
        badge_code="GJ-POL-101",
        mfa_enabled=True
    ),
    User(
        id="usr_rtoadmin",
        name="Comm. Sunil Mehta",
        email="rtoadmin@platform.gov.in",
        username="rtoadmin",
        password_hash="rto123",
        role=UserRole.DEPARTMENT_ADMIN,
        role_title="Regional Transport Officer",
        department_id="DEPT-03",
        department_name="Regional Transport Office Gujarat (RTO)",
        badge_code="GJ-RTO-202",
        mfa_enabled=True
    ),
    User(
        id="usr_aianalyst",
        name="Insp. Vikram Parmar",
        email="aianalyst@platform.gov.in",
        username="analyst",
        password_hash="ai123",
        role=UserRole.AI_ANALYST,
        role_title="ATS Law Enforcement AI Specialist",
        department_id="DEPT-01",
        department_name="Gujarat Police Department",
        badge_code="GJ-ATS-882"
    ),
    User(
        id="usr_gismap",
        name="Eng. Priya Vaghela",
        email="gismap@platform.gov.in",
        username="gis",
        password_hash="gis123",
        role=UserRole.GIS_OPERATOR,
        role_title="Spatial Mapping & PostGIS Specialist",
        department_id=None,
        department_name="State GIS Mapping Directorate",
        badge_code="GJ-GIS-505"
    ),
    User(
        id="usr_maintops",
        name="Manager Jayesh Patel",
        email="maintops@platform.gov.in",
        username="maint",
        password_hash="maint123",
        role=UserRole.MAINTENANCE_OFFICER,
        role_title="Field Operations & SLA Manager",
        department_id=None,
        department_name="AMC Vendor Control Cell",
        badge_code="GJ-OPS-404"
    ),
    User(
        id="usr_techfield",
        name="Tech. Bhavik Shah",
        email="techfield@platform.gov.in",
        username="tech",
        password_hash="tech123",
        role=UserRole.TECHNICIAN,
        role_title="Field Service Engineer",
        department_id=None,
        department_name="Axis Communications Field Team",
        badge_code="GJ-TECH-302"
    ),
    User(
        id="usr_operator",
        name="Operator Subodh Kothari",
        email="operator@platform.gov.in",
        username="operator",
        password_hash="operator123",
        role=UserRole.OPERATOR,
        role_title="Department Monitoring Operator",
        department_id=None,
        department_name="Department Monitoring Pool",
        is_active=True,
        status="ACTIVE"
    ),
    User(
        id="usr_pending_police",
        name="Officer Ramesh Desai",
        email="ramesh.desai@police.gov.in",
        username="ramesh_desai",
        password_hash="RameshPass123!",
        role=UserRole.OPERATOR,
        role_title="Department Monitoring Operator (Pending Approval)",
        department_id="DEPT-01",
        department_name="Gujarat Police Department",
        badge_code="GJ-OP-901",
        is_active=False,
        status="PENDING_APPROVAL",
        created_at="2026-09-05 11:30:00"
    ),
    User(
        id="usr_pending_rto",
        name="Insp. Sunita Patel",
        email="sunita.patel@rto.gov.in",
        username="sunita_rto",
        password_hash="SunitaPass123!",
        role=UserRole.OPERATOR,
        role_title="Department Monitoring Operator (Pending Approval)",
        department_id="DEPT-03",
        department_name="Regional Transport Office Gujarat (RTO)",
        badge_code="GJ-OP-902",
        is_active=False,
        status="PENDING_APPROVAL",
        created_at="2026-09-05 12:15:00"
    ),
    User(
        id="usr_pending_transport",
        name="Officer Vikram Solanki",
        email="vikram.solanki@transport.gov.in",
        username="vikram_transport",
        password_hash="VikramPass123!",
        role=UserRole.OPERATOR,
        role_title="Department Monitoring Operator (Pending Approval)",
        department_id="DEPT-02",
        department_name="Gujarat State Transport Corp (GSRTC)",
        badge_code="GJ-OP-903",
        is_active=False,
        status="PENDING_APPROVAL",
        created_at="2026-09-05 12:45:00"
    )
]

DEPARTMENTS_CONFIG = [
    ("DEPT-01", "Gujarat Police Department", "POL", "Law Enforcement", "Comm. Rajesh Patel", "police.nodal@gujarat.gov.in"),
    ("DEPT-02", "Gujarat State Transport Corp (GSRTC)", "TRN", "Transit & Highways", "Dr. Anita Shah", "transport.nodal@gujarat.gov.in"),
    ("DEPT-03", "Regional Transport Office Gujarat (RTO)", "RTO", "Vehicle Licensing", "Sunil Mehta", "rto.nodal@gujarat.gov.in"),
    ("DEPT-04", "Food, Civil Supplies & Consumer Affairs", "FCS", "Godowns & PDS", "Meena Joshi", "supplies.nodal@gujarat.gov.in"),
    ("DEPT-05", "Ahmedabad & Surat Municipal Corps", "MC", "Urban Infrastructure", "Vikram Parmar", "municipal.nodal@gujarat.gov.in"),
    ("DEPT-06", "Health & Family Welfare Dept Gujarat", "HFW", "Hospitals & Clinics", "Dr. S. K. Trivedi", "health.nodal@gujarat.gov.in"),
    ("DEPT-07", "Gujarat State Disaster Management Authority", "GSDMA", "Emergency Services", "Col. R. S. Solanki", "disaster.nodal@gujarat.gov.in"),
    ("DEPT-08", "Forest & Environment Dept (Gir & Parks)", "FOR", "Wildlife & Parks", "Priya Vaghela", "forest.nodal@gujarat.gov.in"),
    ("DEPT-09", "State Prohibition & Excise Department", "EXC", "Checkposts & Revenue", "Arun Jadejha", "excise.nodal@gujarat.gov.in"),
    ("DEPT-10", "Public Works Department Gujarat (PWD)", "PWD", "Roads & Bridges", "Eng. H. N. Raval", "pwd.nodal@gujarat.gov.in"),
    ("DEPT-11", "Revenue & Land Records Dept", "REV", "Administrative Hubs", "Aakash Desai", "revenue.nodal@gujarat.gov.in"),
    ("DEPT-12", "Gujarat Maritime Board (GMB Ports)", "GMB", "Coastal Security & Ports", "Capt. V. K. Gohil", "ports.nodal@gujarat.gov.in"),
    ("DEPT-13", "Urban Development & Urban Housing", "UDD", "Smart Cities", "Sanjay Chaudhari", "urban.nodal@gujarat.gov.in"),
    ("DEPT-14", "School Education & Samagra Shiksha", "SED", "School Security", "Kavita Bhatt", "school.nodal@gujarat.gov.in"),
    ("DEPT-15", "Higher & Technical Education Dept", "HTE", "Universities", "Prof. P. B. Dave", "education.nodal@gujarat.gov.in"),
    ("DEPT-16", "Social Justice & Empowerment", "SJD", "Shelter & Welfare", "Ramesh Rathod", "social.nodal@gujarat.gov.in"),
    ("DEPT-17", "Women & Child Development Dept", "WCD", "Child Welfare", "Shalini Vyas", "wcd.nodal@gujarat.gov.in"),
    ("DEPT-18", "Tourism Corporation of Gujarat (TCGL)", "TCGL", "Heritage Sites", "Rahul Panday", "tourism.nodal@gujarat.gov.in"),
    ("DEPT-19", "Industries & Mines Dept (GIDC)", "IND", "Industrial Parks", "Deepak Barot", "industry.nodal@gujarat.gov.in"),
    ("DEPT-20", "Agriculture, Farmers Welfare & Co-operation", "AGR", "APMC Markets", "Ganesh Zala", "agri.nodal@gujarat.gov.in"),
    ("DEPT-21", "Water Resources & Narmada Water", "WRD", "Dams & Reservoirs", "Eng. M. L. Sanghavi", "water.nodal@gujarat.gov.in"),
    ("DEPT-22", "Energy & Petrochemicals Dept (GETCO)", "EPG", "Substations & Grids", "Nitin Dabhi", "energy.nodal@gujarat.gov.in"),
    ("DEPT-23", "Science & Technology Dept (DST)", "DST", "Data Centers & GIFT City", "Sameer Thakar", "it.nodal@gujarat.gov.in"),
    ("DEPT-24", "Prisons & Correctional Services Gujarat", "PCS", "Perimeter Security", "Supt. A. K. Makwana", "prisons.nodal@gujarat.gov.in"),
    ("DEPT-25", "Labour, Skill Development & Employment", "LED", "Worksite Safety", "Vandana Bhabhor", "labour.nodal@gujarat.gov.in"),
    ("DEPT-26", "Finance Department Gujarat", "FIN", "High Security Vaults", "Subodh Kothari", "finance.nodal@gujarat.gov.in"),
]

# Major Districts across Gujarat
DISTRICTS = [
    ("Ahmedabad Metro", 23.0225, 72.5714),
    ("Gandhinagar Capital", 23.2156, 72.6369),
    ("Surat Urban", 21.1702, 72.8311),
    ("Vadodara City", 22.3072, 73.1812),
    ("Rajkot Metro", 22.3039, 70.8022),
    ("Bhavnagar Coastal", 21.7645, 72.1519),
    ("Jamnagar Industrial", 22.4707, 70.0577),
    ("Junagadh / Gir", 21.5222, 70.4579),
    ("Anand & Kheda", 22.5645, 72.9289),
    ("Bharuch & Narmada", 21.7051, 72.9959),
    ("Kutch & Bhuj Border", 23.2420, 69.6669),
    ("Porbandar Port", 21.6417, 69.6293),
]

CAMERA_TYPES = ["IP Bullet", "IP Dome", "PTZ Speed Dome", "Thermal InfraRed", "ANPR / LPR Dedicated", "360 Panoramic", "Starlight Night Vision"]
STORAGE_ARCHS = ["Local NVR", "On-premise Server", "Hybrid", "Central Cloud"]
LINK_TYPES = ["Fibre Optic", "Gigabit Broadband", "Dedicated Leased Line", "Industrial 5G/4G"]
PROTOCOLS = ["RTSP", "ONVIF Profile S", "ONVIF Profile G", "ONVIF Profile T", "WebRTC", "HLS Stream"]
VENDORS = ["Axis Communications", "Hikvision Enterprise", "Dahua Technology", "Hanwha Vision", "Bosch Security", "Uniview", "Honeywell Security"]
OWNERSHIPS = ["Government Owned", "Private Public-Facing", "Commercial Mall", "Housing Society"]

OFFICER_SURNAMES = ["Patel", "Shah", "Mehta", "Trivedi", "Joshi", "Parmar", "Solanki", "Desai", "Raval", "Vaghela"]

def generate_seed_data() -> Tuple[List[Department], List[Camera], List[AnprDetection], List[WatchlistItem], List[MaintenanceTicket], List[AuditLog]]:
    departments = [
        Department(
            id=d[0], name=d[1], code=d[2], category=d[3],
            nodal_officer=d[4], contact_email=d[5]
        ) for d in DEPARTMENTS_CONFIG
    ]

    cameras: List[Camera] = []
    tickets: List[MaintenanceTicket] = []
    audit_logs: List[AuditLog] = []

    now = datetime.now(timezone.utc)

    # Generate 520 realistic cameras across Gujarat
    cam_index = 1
    for dept in departments:
        cams_for_dept = 20 if dept.id in ["DEPT-01", "DEPT-02", "DEPT-05"] else random.randint(18, 22)
        for _ in range(cams_for_dept):
            district_name, base_lat, base_lng = random.choice(DISTRICTS)
            # Add small random spatial jitter
            lat_jitter = random.uniform(-0.035, 0.035)
            lng_jitter = random.uniform(-0.035, 0.035)
            lat = round(base_lat + lat_jitter, 6)
            lng = round(base_lng + lng_jitter, 6)

            cam_id = f"CAM-{cam_index:04d}"
            asset_code = f"GJ-GOV-CAM-{2024}-{cam_index:04d}"
            cam_type = random.choice(CAMERA_TYPES)
            is_online = random.random() > 0.12 # 88% online
            status = "Active" if is_online else random.choice(["Fault/Repair", "Maintenance Due", "Active"])
            
            health = random.randint(85, 100) if is_online else random.randint(10, 55)

            amc_year = random.choice([2024, 2025, 2026])
            amc_month = random.randint(1, 12)
            amc_expiry = f"{amc_year}-{amc_month:02d}-28"
            warranty_status = "Active" if amc_year >= 2025 else "Expired"

            camera = Camera(
                id=cam_id,
                asset_code=asset_code,
                name=f"{dept.code} Node #{cam_index:03d} ({district_name})",
                dept_id=dept.id,
                dept_name=dept.name,
                station_division=f"{district_name} Division",
                responsible_officer=f"Insp. {random.choice(OFFICER_SURNAMES)}",
                officer_phone=f"+91 98980 {random.randint(10000, 99999)}",
                state="Gujarat",
                district=district_name,
                taluka=f"{district_name} Zone",
                ward_zone=f"Ward {random.randint(1, 20)}",
                latitude=lat,
                longitude=lng,
                altitude=round(random.uniform(12.0, 50.0), 1),
                fov_azimuth=round(random.uniform(0.0, 359.0), 1),
                fov_angle=random.choice([45.0, 60.0, 90.0, 120.0]),
                coverage_radius=random.choice([100.0, 150.0, 200.0, 250.0]),
                camera_type=cam_type,
                resolution=random.choice(["1080p Full HD", "4K Ultra HD", "4MP QHD"]),
                fps=random.choice([25, 30, 60]),
                bitrate_kbps=random.choice([2048, 4096, 8192]),
                storage_arch=random.choice(STORAGE_ARCHS),
                nvr_ip=f"10.{random.randint(10, 199)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
                nvr_port=554,
                storage_tb=random.choice([4.0, 8.0, 16.0, 32.0]),
                retention_days=random.choice([15, 30, 60, 90]),
                link_type=random.choice(LINK_TYPES),
                bandwidth_mbps=random.choice([50, 100, 500, 1000]),
                protocol=random.choice(PROTOCOLS),
                stream_url=f"https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                ownership=random.choice(OWNERSHIPS),
                vendor_name=random.choice(VENDORS),
                amc_expiry=amc_expiry,
                warranty_status=warranty_status,
                status=status,
                is_online=is_online,
                last_ping=(now - timedelta(minutes=random.randint(1, 45))).strftime("%Y-%m-%d %H:%M:%S"),
                health_score=health
            )
            cameras.append(camera)

            audit_logs.append(AuditLog(
                id=f"AUD-{cam_index:04d}",
                camera_id=cam_id,
                timestamp=(now - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d %H:%M:%S"),
                user_id="USR-ADMIN-01",
                user_name="Gujarat Control Supervisor",
                role="SUPER_ADMIN",
                action_type="STATE_TRANSITION",
                previous_state="Installed",
                new_state=status,
                justification="State CCTV registry onboarding validation."
            ))

            if not is_online or status == "Fault/Repair":
                severity = random.choice(["Critical", "High", "Medium", "Low"])
                sla_hours = {"Critical": 2, "High": 6, "Medium": 24, "Low": 48}[severity]
                created_dt = now - timedelta(hours=random.randint(2, 20))
                ticket = MaintenanceTicket(
                    id=f"TKT-{len(tickets)+1:04d}",
                    ticket_code=f"GJ-INC-{2024}-{len(tickets)+1:04d}",
                    camera_id=cam_id,
                    camera_name=camera.name,
                    dept_id=dept.id,
                    dept_name=dept.name,
                    issue_type=random.choice(["No Video Stream Signal", "Network Loss / High Latency", "PTZ Motor Failure", "IR Illuminator Fault", "Power Surge Issue"]),
                    severity=severity,
                    status=random.choice(["Open", "Assigned", "In Progress"]),
                    created_at=created_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    sla_due_at=(created_dt + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S"),
                    assigned_technician_id="usr_techfield",
                    assigned_technician_name=f"Tech. {random.choice(['Jayesh Patel', 'Bhavik Shah', 'Chirag Raval', 'Hardik Joshi'])}",
                    vendor_name=camera.vendor_name,
                    repair_cost_inr=float(random.randint(2500, 18500)),
                    photo_evidence_url="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&q=80"
                )
                tickets.append(ticket)

            cam_index += 1

    # Update camera counts in departments
    for dept in departments:
        dept_cams = [c for c in cameras if c.dept_id == dept.id]
        dept.total_cameras = len(dept_cams)
        dept.active_cameras = len([c for c in dept_cams if c.is_online])

    # Seed Gujarat Watchlist (GJ Plates)
    watchlist = [
        WatchlistItem("W-01", "GJ-01-AB-1234", "Stolen Vehicle", "Black SUV involved in heist case near SG Highway Ahmedabad", "Crime Branch Ahmedabad", (now - timedelta(days=2)).strftime("%Y-%m-%d"), "Critical"),
        WatchlistItem("W-02", "GJ-05-XY-9876", "Wanted Suspect", "White Sedan associated with contraband smuggling in Surat", "ATS Gujarat Unit", (now - timedelta(days=5)).strftime("%Y-%m-%d"), "Critical"),
        WatchlistItem("W-03", "GJ-06-DE-5555", "Blacklisted Truck", "Illegal mineral dumper truck near Vadodara highway", "Gujarat RTO Flying Squad", (now - timedelta(days=1)).strftime("%Y-%m-%d"), "High"),
        WatchlistItem("W-04", "GJ-18-GH-7788", "Missing Person", "Silver Hatchback last driven near Gandhinagar Capital", "Cyber Crime Cell", (now - timedelta(days=3)).strftime("%Y-%m-%d"), "Medium"),
    ]

    # Seed ANPR Detections across Gujarat Cities (Ahmedabad, Gandhinagar, Surat, Vadodara, Rajkot)
    anpr_detections: List[AnprDetection] = []
    anpr_id_counter = 1

    target_plates = [
        ("GJ-01-AB-1234", "SUV", "Black", True, "Stolen Vehicle"),
        ("GJ-05-XY-9876", "Sedan", "White", True, "Wanted Suspect"),
        ("GJ-06-DE-5555", "Commercial Truck", "Yellow/Blue", True, "Blacklisted Truck"),
        ("GJ-03-CZ-4321", "Sedan", "Silver", False, None),
        ("GJ-12-EF-8899", "Hatchback", "Red", False, None),
        ("GJ-18-KL-2468", "SUV", "Dark Blue", False, None),
    ]

    gujarat_cams = [c for c in cameras if any(city in c.district for city in ["Ahmedabad", "Gandhinagar", "Surat", "Vadodara", "Rajkot"])]

    for plate, vtype, color, is_watch, watch_cat in target_plates:
        route_cams = random.sample(gujarat_cams, k=min(8, len(gujarat_cams)))
        start_time = now - timedelta(hours=random.randint(4, 36))
        for i, cam in enumerate(route_cams):
            det_time = start_time + timedelta(minutes=i * random.randint(15, 45))
            anpr_detections.append(AnprDetection(
                id=f"ANPR-{anpr_id_counter:06d}",
                camera_id=cam.id,
                camera_name=cam.name,
                dept_name=cam.dept_name,
                latitude=cam.latitude,
                longitude=cam.longitude,
                plate_number=plate,
                vehicle_type=vtype,
                vehicle_color=color,
                confidence=round(random.uniform(0.91, 0.99), 3),
                timestamp=det_time.strftime("%Y-%m-%d %H:%M:%S"),
                snapshot_url="https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400&q=80",
                is_watchlist_hit=is_watch,
                watchlist_category=watch_cat
            ))
            anpr_id_counter += 1

    # Random background ANPR detections across Gujarat
    for _ in range(130):
        cam = random.choice(cameras)
        det_time = now - timedelta(hours=random.randint(1, 48))
        plate_no = f"GJ-{random.choice(['01','03','05','06','12','18'])}-{random.choice(['AX','BK','CL','DR'])}-{random.randint(1000, 9999)}"
        anpr_detections.append(AnprDetection(
            id=f"ANPR-{anpr_id_counter:06d}",
            camera_id=cam.id,
            camera_name=cam.name,
            dept_name=cam.dept_name,
            latitude=cam.latitude,
            longitude=cam.longitude,
            plate_number=plate_no,
            vehicle_type=random.choice(["Sedan", "SUV", "Hatchback", "Motorcycle", "Commercial Truck", "Bus"]),
            vehicle_color=random.choice(["White", "Black", "Silver", "Red", "Blue", "Grey"]),
            confidence=round(random.uniform(0.88, 0.99), 3),
            timestamp=det_time.strftime("%Y-%m-%d %H:%M:%S"),
            snapshot_url="https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400&q=80",
            is_watchlist_hit=False
        ))
        anpr_id_counter += 1

    anpr_detections.sort(key=lambda x: x.timestamp, reverse=True)

    return departments, cameras, anpr_detections, watchlist, tickets, audit_logs
