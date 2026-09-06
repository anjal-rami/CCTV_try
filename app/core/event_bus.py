"""
Decoupled Event & Metadata Message Bus with DLQ and In-Memory / Redis Streams Fallback.
Topics:
- cctv.events.detections: ANPR matches, object detections, polygon intrusions
- cctv.events.camera_status: Online/Offline/Degraded heartbeats
- cctv.events.alerts: Rule-triggered operational emergencies
"""
import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timezone

from backend.models import FederatedEvent

logger = logging.getLogger("cctv.event_bus")

TOPIC_DETECTIONS = "cctv.events.detections"
TOPIC_CAMERA_STATUS = "cctv.events.camera_status"
TOPIC_ALERTS = "cctv.events.alerts"

ALL_TOPICS = [TOPIC_DETECTIONS, TOPIC_CAMERA_STATUS, TOPIC_ALERTS]

class EventBus:
    """
    Asynchronous event bus supporting topic dispatch, dead-letter queue (DLQ),
    and fast in-memory replay buffer.
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {
            TOPIC_DETECTIONS: [],
            TOPIC_CAMERA_STATUS: [],
            TOPIC_ALERTS: []
        }
        self.published_events: List[FederatedEvent] = []
        self.dlq_events: List[Dict[str, Any]] = []
        self.max_history: int = 1000

    def subscribe(self, topic: str, handler: Callable):
        """Register a subscriber handler for a topic."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(handler)

    async def publish(self, topic: str, event_data: Any) -> bool:
        """
        Publish an event to a topic.
        Dispatches to subscribers and records to DLQ on failure.
        """
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    def _to_federated_event(self, topic: str, event_data: Any) -> Optional[FederatedEvent]:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(event_data, dict):
            event_id = event_data.get("id") or event_data.get("event_id") or f"EVT-BUS-{len(self.published_events)+1:05d}"
            return FederatedEvent(
                id=event_id,
                vms_platform_id=event_data.get("vms_platform_id", "VMS-LOCAL"),
                vms_name=event_data.get("vms_name", "Local VMS"),
                vendor=event_data.get("vendor", "Generic"),
                camera_id=event_data.get("camera_id", "CAM-UNKNOWN"),
                camera_name=event_data.get("camera_name", "Camera Node"),
                department_id=event_data.get("department_id", "DEPT-01"),
                department_name=event_data.get("department_name", "Command Control"),
                topic=topic,
                event_type=event_data.get("event_type", "GENERIC_EVENT"),
                severity=event_data.get("severity", "INFO"),
                timestamp=event_data.get("timestamp", now_str),
                plate_number=event_data.get("plate_number"),
                confidence=float(event_data.get("confidence", 0.95)),
                payload=event_data.get("payload", {})
            )
        elif isinstance(event_data, FederatedEvent):
            return event_data
        return None

    def _dispatch_sync_handlers(self, topic: str, fed_event: FederatedEvent, event_data: Any):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.published_events.insert(0, fed_event)
        if len(self.published_events) > self.max_history:
            self.published_events.pop()

        handlers = self.subscribers.get(topic, [])
        for handler in handlers:
            try:
                if not asyncio.iscoroutinefunction(handler):
                    handler(fed_event)
            except Exception as ex:
                logger.error(f"Event dispatch failure on topic {topic}: {ex}")
                self.dlq_events.append({
                    "failed_at": now_str,
                    "topic": topic,
                    "event_id": fed_event.id,
                    "error": str(ex),
                    "payload": event_data if isinstance(event_data, dict) else fed_event.__dict__,
                    "retry_count": 0
                })

    async def publish(self, topic: str, event_data: Any) -> bool:
        """
        Publish an event to a topic asynchronously.
        """
        fed_event = self._to_federated_event(topic, event_data)
        if not fed_event:
            return False

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.published_events.insert(0, fed_event)
        if len(self.published_events) > self.max_history:
            self.published_events.pop()

        handlers = self.subscribers.get(topic, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(fed_event)
                else:
                    handler(fed_event)
            except Exception as ex:
                logger.error(f"Event dispatch failure on topic {topic}: {ex}")
                self.dlq_events.append({
                    "failed_at": now_str,
                    "topic": topic,
                    "event_id": fed_event.id,
                    "error": str(ex),
                    "payload": event_data if isinstance(event_data, dict) else fed_event.__dict__,
                    "retry_count": 0
                })
        return True

    def publish_sync(self, topic: str, event_data: Any) -> bool:
        """Synchronous publisher for event ingestion and workers."""
        fed_event = self._to_federated_event(topic, event_data)
        if not fed_event:
            return False
        self._dispatch_sync_handlers(topic, fed_event, event_data)
        return True

    def get_events(self, limit: int = 100, topic: Optional[str] = None) -> List[FederatedEvent]:
        """Fetch recent events from bus buffer."""
        if topic:
            return [e for e in self.published_events if e.topic == topic][:limit]
        return self.published_events[:limit]

    def get_dlq(self) -> List[Dict[str, Any]]:
        """Return events currently in dead-letter queue."""
        return self.dlq_events

# Global singleton event bus
event_bus = EventBus()
