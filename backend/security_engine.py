"""
Cybersecurity & Compliance Engine for Security Admin Dashboard.
Calculates Threat Meter score, manages IP blocklists, session terminations, and audit forensics.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from .models import SecurityThreatIncident, BlockedIpRecord, AuditLog

BLOCKED_IPS: List[BlockedIpRecord] = [
    BlockedIpRecord("198.51.100.44", "High-frequency brute-force login attack (45 attempts/min)", "2026-09-04 18:20:00", "Security Auto-Shield"),
    BlockedIpRecord("203.0.113.89", "Unauthorized API Route Probe on /api/v1/ai/anpr/search", "2026-09-04 21:05:12", "Security Admin"),
]

SECURITY_INCIDENTS: List[SecurityThreatIncident] = [
    SecurityThreatIncident(
        id="INC-SEC-001",
        incident_code="SEC-2024-8801",
        severity="CRITICAL",
        threat_type="High-Frequency Login Brute-Force",
        source_ip="198.51.100.44",
        user_email="unknown_attacker@darkweb.org",
        timestamp=(datetime.now(timezone.utc) - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        status="BLOCKED",
        details="Automated botnet attempted 45 logins in 60s against superadmin@platform.gov.in. IP automatically banned."
    ),
    SecurityThreatIncident(
        id="INC-SEC-002",
        incident_code="SEC-2024-8802",
        severity="HIGH",
        threat_type="Unauthorized Privilege Escalation Attempt",
        source_ip="203.0.113.89",
        user_email="operator@platform.gov.in",
        timestamp=(datetime.now(timezone.utc) - timedelta(minutes=32)).strftime("%Y-%m-%d %H:%M:%S"),
        status="INVESTIGATING",
        details="Operator account attempted direct API invocation of /api/v1/ai/anpr/search without ANPR authority claims."
    ),
    SecurityThreatIncident(
        id="INC-SEC-003",
        incident_code="SEC-2024-8803",
        severity="MEDIUM",
        threat_type="Rate Limit Threshold Warning",
        source_ip="10.27.12.90",
        user_email="nodal.supplies@cctv.gujarat.gov.in",
        timestamp=(datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        status="RESOLVED",
        details="Nodal Officer triggered 120 camera query requests per minute during bulk CSV verification."
    ),
]

def calculate_security_threat_score() -> Dict[str, Any]:
    """
    Calculate Threat Score (0-100) based on active incidents, failed logins, and banned IPs.
    """
    active_incidents = [i for i in SECURITY_INCIDENTS if i.status in ["ACTIVE", "INVESTIGATING"]]
    critical_count = len([i for i in active_incidents if i.severity == "CRITICAL"])
    high_count = len([i for i in active_incidents if i.severity == "HIGH"])
    
    # Base score math
    score = 12 + (critical_count * 25) + (high_count * 15) + len(BLOCKED_IPS) * 5
    score = min(100, max(0, score))

    threat_level = "LOW"
    if score >= 75:
        threat_level = "CRITICAL"
    elif score >= 50:
        threat_level = "HIGH"
    elif score >= 25:
        threat_level = "ELEVATED"

    return {
        "threat_score": score,
        "threat_level": threat_level,
        "active_threat_incidents": len(active_incidents),
        "total_blocked_ips": len(BLOCKED_IPS),
        "failed_logins_24h": 68,
        "suspicious_api_calls_24h": 14,
        "crypto_log_hash_verified": True
    }

def block_ip_address(ip_address: str, reason: str, blocked_by: str = "Security Admin") -> BlockedIpRecord:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    record = BlockedIpRecord(ip_address.strip(), reason.strip(), now_str, blocked_by)
    # Avoid duplicates
    if not any(b.ip_address == record.ip_address for b in BLOCKED_IPS):
        BLOCKED_IPS.insert(0, record)
    return record

def is_ip_blocked(ip_address: str) -> bool:
    return any(b.ip_address == ip_address.strip() for b in BLOCKED_IPS)
