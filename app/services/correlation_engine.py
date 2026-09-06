"""
Cross-System Operational Event-Correlation Engine.
Implements:
- Rule 1 (Spatial/Temporal): Same plate/signature across two different VMS platforms within N-minute window.
- Rule 2 (Department Escalation): Triggers multi-agency notification & automated workflow task when boundary crossed.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from backend.models import FederatedEvent, CorrelatedIncident, WorkflowTask
from app.core.event_bus import event_bus, TOPIC_DETECTIONS, TOPIC_ALERTS

class CorrelationEngine:
    def __init__(self, time_window_minutes: int = 15):
        self.time_window_minutes = time_window_minutes
        self.correlated_incidents: List[CorrelatedIncident] = []
        self.workflows: List[WorkflowTask] = []

    def parse_time(self, ts_str: str) -> datetime:
        try:
            return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    def correlate(self, new_event: FederatedEvent) -> Optional[CorrelatedIncident]:
        """
        Evaluate Rule 1 and Rule 2 against event bus history.
        """
        if not new_event.plate_number:
            return None

        clean_plate = new_event.plate_number.strip().upper()
        now_dt = self.parse_time(new_event.timestamp)
        cutoff_dt = now_dt - timedelta(minutes=self.time_window_minutes)

        # Scan recent events in event bus buffer
        past_candidates = [
            e for e in event_bus.published_events
            if e.id != new_event.id and e.plate_number and e.plate_number.strip().upper() == clean_plate
        ]

        # Filter for candidates within time window and from a DIFFERENT VMS platform (Rule 1)
        cross_vms_matches = [
            e for e in past_candidates
            if e.vms_platform_id != new_event.vms_platform_id and self.parse_time(e.timestamp) >= cutoff_dt
        ]

        if not cross_vms_matches:
            return None

        # Sort match by time
        primary_match = sorted(cross_vms_matches, key=lambda x: self.parse_time(x.timestamp))[0]
        prev_dt = self.parse_time(primary_match.timestamp)
        elapsed_mins = max(0.1, round(abs((now_dt - prev_dt).total_seconds() / 60.0), 1))

        # Check existing correlation to prevent duplicate flooding
        existing = next((
            c for c in self.correlated_incidents 
            if c.plate_number == clean_plate and abs((now_dt - self.parse_time(c.last_detected_at)).total_seconds()) < 3600
        ), None)

        if existing:
            existing.event_count += 1
            existing.last_detected_at = new_event.timestamp
            if new_event.vms_platform_id not in existing.source_vms_ids:
                existing.source_vms_ids.append(new_event.vms_platform_id)
            if new_event.department_name not in existing.departments_involved:
                existing.departments_involved.append(new_event.department_name)
            return existing

        # Rule 2: Department Escalation
        is_cross_dept = new_event.department_id != primary_match.department_id
        corr_type = "CROSS_DEPARTMENT_ESCALATION" if is_cross_dept else "SPATIAL_TEMPORAL"

        incident_id = f"CORR-{len(self.correlated_incidents)+1:04d}"
        title = f"Multi-VMS Alert: Plate '{clean_plate}' tracked across {primary_match.vms_name} and {new_event.vms_name}"
        details = (
            f"Target vehicle {clean_plate} detected at {primary_match.camera_name} ({primary_match.vendor} VMS) "
            f"then tracked {elapsed_mins} mins later at {new_event.camera_name} ({new_event.vendor} VMS). "
            f"Cross-agency boundary traversed: {primary_match.department_name} -> {new_event.department_name}."
        )

        incident = CorrelatedIncident(
            id=incident_id,
            title=title,
            correlation_type=corr_type,
            source_vms_ids=[primary_match.vms_platform_id, new_event.vms_platform_id],
            departments_involved=[primary_match.department_name, new_event.department_name],
            plate_number=clean_plate,
            confidence=round(min(primary_match.confidence, new_event.confidence), 2),
            severity="CRITICAL",
            first_detected_at=primary_match.timestamp,
            last_detected_at=new_event.timestamp,
            time_window_minutes=elapsed_mins,
            event_count=2,
            details=details,
            events=[primary_match.__dict__, new_event.__dict__],
            status="OPEN"
        )

        # Automatically spawn cross-department workflow task
        wf_id = f"WF-TASK-{len(self.workflows)+1:04d}"
        incident.workflow_task_id = wf_id

        deadline_str = (now_dt + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        workflow = WorkflowTask(
            id=wf_id,
            title=f"Multi-Agency Intercept Order: {clean_plate}",
            event_id=new_event.id,
            correlation_id=incident_id,
            source_department=primary_match.department_name,
            assigned_department=new_event.department_name,
            priority="CRITICAL",
            status="OPEN",
            sop_checklist=[
                {"id": 1, "task": "Verify cross-VMS camera stream live timestamp", "completed": True, "verified_by": "Automated Correlation Engine"},
                {"id": 2, "task": "Dispatch local patrol / field unit to target corridor", "completed": False, "verified_by": None},
                {"id": 3, "task": "Notify municipal traffic control to lock down exit signals", "completed": False, "verified_by": None},
                {"id": 4, "task": "Log incident report & archive evidence clips", "completed": False, "verified_by": None}
            ],
            escalation_deadline=deadline_str,
            created_at=new_event.timestamp,
            notes=f"Triggered by automated correlation {incident_id}. Requires multi-department coordination."
        )

        self.workflows.insert(0, workflow)
        self.correlated_incidents.insert(0, incident)

        # Notify event bus on alerts topic
        event_bus.publish_sync(TOPIC_ALERTS, {
            "id": f"EVT-CORR-{incident_id}",
            "vms_platform_id": "FEDERATION-HUB",
            "vms_name": "Integrated CCTV Federation Hub",
            "vendor": "CorrelationEngine",
            "camera_id": new_event.camera_id,
            "camera_name": new_event.camera_name,
            "department_id": new_event.department_id,
            "department_name": new_event.department_name,
            "event_type": "CROSS_VMS_CORRELATION",
            "severity": "CRITICAL",
            "timestamp": new_event.timestamp,
            "plate_number": clean_plate,
            "confidence": incident.confidence,
            "payload": {"incident_id": incident_id, "workflow_task_id": wf_id}
        })

        return incident

# Global singleton correlation engine
correlation_engine = CorrelationEngine()

# Connect correlation engine to event bus subscriptions
event_bus.subscribe(TOPIC_DETECTIONS, correlation_engine.correlate)
event_bus.subscribe(TOPIC_ALERTS, correlation_engine.correlate)
