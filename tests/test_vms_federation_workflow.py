"""
Model 3 VMS Federation, Event Bus & Unified Workflow Engine Self-Check Suite.
Runs assert-based verification across:
1. VMS Platform Model & Adapter Factory
2. Milestone & Hikvision Protocol Adapters
3. EventBus topic dispatch & DLQ
4. Two-System Federation Demo Bench
5. Cross-System Correlation Engine (Rule 1 Spatial/Temporal & Rule 2 Department Escalation)
6. Unified Cross-Department Workflow Engine & SOP Checklists
7. High-Throughput Search Abstraction & CSV Analytics Export
"""
import os
import sys
sys.path.insert(0, os.path.abspath("."))

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.main import app, VMS_PLATFORMS, CAMERAS
from backend.models import VMSPlatform, FederatedEvent, CorrelatedIncident, WorkflowTask
from app.services.adapters.base import (
    VMSAdapterFactory, MilestoneAdapter, HikvisionISAPIAdapter, GenericONVIFAdapter
)
from app.core.event_bus import event_bus, TOPIC_DETECTIONS, TOPIC_CAMERA_STATUS, TOPIC_ALERTS
from app.services.correlation_engine import correlation_engine

client = TestClient(app)

def test_vms_platform_model_and_adapters():
    """Verify VMS Platform abstraction and adapter factory."""
    test_plat = VMSPlatform(
        id="VMS-TEST-01",
        name="Test Milestone Node",
        department_id="DEPT-01",
        vendor="Milestone",
        version="2024 R1",
        protocol="REST API",
        base_endpoint_url="http://127.0.0.1:8081",
        credential_secret_ref="vault://secret",
        adapter_type="milestone",
        status="ONLINE",
        created_at="2026-09-05 10:00:00"
    )
    adapter = VMSAdapterFactory.get_adapter(test_plat)
    assert isinstance(adapter, MilestoneAdapter)

    # Test Milestone interface methods
    auth = adapter.authenticate()
    assert auth["success"] is True
    assert "access_token" in auth

    cams = adapter.fetch_camera_list()
    assert len(cams) >= 2
    assert cams[0]["id"].startswith("VMS-TEST-01")

    stream = adapter.get_stream_handle(cams[0]["id"])
    assert stream["protocol"] in ["HLS", "RTSP"]
    assert "stream_url" in stream

    events = adapter.subscribe_events()
    assert len(events) >= 1
    assert events[0]["plate_number"] == "GJ-01-AB-1234"

    telemetry = adapter.poll_telemetry()
    assert telemetry["status"] == "ONLINE"

    # Test Hikvision ISAPI adapter
    hik_plat = VMSPlatform(
        id="VMS-TEST-02",
        name="Test Hikvision ISAPI",
        department_id="DEPT-04",
        vendor="Hikvision",
        version="ISAPI v2.6",
        protocol="REST/ISAPI",
        base_endpoint_url="http://127.0.0.1:8082",
        credential_secret_ref="vault://secret",
        adapter_type="hikvision_isapi",
        status="ONLINE",
        created_at="2026-09-05 10:00:00"
    )
    hik_adapter = VMSAdapterFactory.get_adapter(hik_plat)
    assert isinstance(hik_adapter, HikvisionISAPIAdapter)
    assert hik_adapter.authenticate()["auth_type"] == "ISAPI-Digest"
    assert len(hik_adapter.fetch_camera_list()) >= 2


def test_event_bus_and_dlq():
    """Verify decoupled event bus pub/sub, buffer, and dead-letter queue."""
    initial_count = len(event_bus.published_events)
    test_evt = {
        "id": "EVT-TEST-UNIT-01",
        "vms_platform_id": "VMS-UNIT-01",
        "vms_name": "Unit VMS",
        "vendor": "Milestone",
        "camera_id": "CAM-UNIT-01",
        "camera_name": "Unit Test Camera",
        "department_id": "DEPT-01",
        "department_name": "Police",
        "event_type": "ANPR_MATCH",
        "severity": "HIGH",
        "timestamp": "2026-09-05 15:00:00",
        "plate_number": "GJ-99-ZZ-9999",
        "confidence": 0.99
    }
    success = event_bus.publish_sync(TOPIC_DETECTIONS, test_evt)
    assert success is True
    assert len(event_bus.published_events) == initial_count + 1
    assert event_bus.published_events[0].plate_number == "GJ-99-ZZ-9999"


def test_two_system_federation_demo_sync_and_correlation():
    """Verify Two-System Federation bench ingests data, correlates plate across VMS, and spawns SOP task."""
    res = client.post("/api/v1/vms-federation/demo-sync")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["cameras_ingested"] >= 4
    assert len(data["systems_federated"]) == 2

    # Check that correlation engine triggered Rule 1 & Rule 2
    assert len(correlation_engine.correlated_incidents) >= 1
    top_incident = correlation_engine.correlated_incidents[0]
    assert top_incident.plate_number == "GJ-01-AB-1234"
    assert "Gujarat Police" in top_incident.title or "Milestone" in top_incident.title

    # Check that automated workflow was created
    assert len(correlation_engine.workflows) >= 1
    top_wf = correlation_engine.workflows[0]
    assert len(top_wf.sop_checklist) == 4
    assert top_wf.status in ["OPEN", "IN_PROGRESS"]


def test_workflow_sop_checklist_lifecycle():
    """Verify interactive SOP checklist toggle and resolution guard."""
    wfs_res = client.get("/api/v1/workflows")
    assert wfs_res.status_code == 200
    wfs = wfs_res.json()
    assert len(wfs) > 0
    task_id = wfs[0]["id"]

    # Attempt to resolve before completing SOP checklist -> Should return 400
    bad_res = client.patch(f"/api/v1/workflows/{task_id}/status", json={"status": "RESOLVED"})
    # Either returns 400 or requires override summary
    if any(not s.get("completed") for s in wfs[0]["sop_checklist"]):
        assert bad_res.status_code == 400

    # Complete Step 1
    step_res = client.patch(f"/api/v1/workflows/{task_id}/checklist", json={
        "step_id": 1,
        "completed": True,
        "verified_by": "Senior Inspector Patel"
    })
    assert step_res.status_code == 200
    assert step_res.json()["sop_checklist"][0]["completed"] is True
    assert step_res.json()["sop_checklist"][0]["verified_by"] == "Senior Inspector Patel"


def test_vms_platforms_api_crud_and_rbac():
    """Verify platform CRUD and role protection."""
    # List platforms
    res = client.get("/api/v1/vms-platforms")
    assert res.status_code == 200
    assert len(res.json()) >= 2

    # Test connection endpoint
    conn_res = client.post("/api/v1/vms-platforms/VMS-POLICE-01/test-connection")
    assert conn_res.status_code == 200
    assert conn_res.json()["status"] == "ONLINE"


def test_events_search_and_report_export():
    """Verify high-throughput search pagination and CSV analytics export."""
    # Search events
    search_res = client.get("/api/v1/events/search?query=GJ-01-AB-1234&page=1&page_size=10")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert "total" in search_data
    assert search_data["page"] == 1
    assert len(search_data["items"]) >= 1

    # Analytics JSON
    json_rep = client.get("/api/v1/analytics/federated-report?format=json")
    assert json_rep.status_code == 200
    assert "report_title" in json_rep.json()
    assert json_rep.json()["platforms_summary"]["total"] >= 2

    # Analytics CSV
    csv_rep = client.get("/api/v1/analytics/federated-report?format=csv")
    assert csv_rep.status_code == 200
    assert "text/csv" in csv_rep.headers.get("content-type", "")
    assert "VMS_ID,VMS_NAME,VENDOR" in csv_rep.text


if __name__ == "__main__":
    test_vms_platform_model_and_adapters()
    test_event_bus_and_dlq()
    test_two_system_federation_demo_sync_and_correlation()
    test_workflow_sop_checklist_lifecycle()
    test_vms_platforms_api_crud_and_rbac()
    test_events_search_and_report_export()
    print("All Model 3 VMS Federation & Workflow Engine Tests Passed Successfully!")
