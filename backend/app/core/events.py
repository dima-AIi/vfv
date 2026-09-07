"""In-process event dispatcher for domain events.

Standard event structure per 10_Event_Architecture.md (#9, #10): every event
carries eventId, eventType, version, timestamp, organizationId, aggregateId,
payload and metadata (correlationId, sourceModule). Business modules build
events through ``build_event`` and hand them off through ``publish_event``.
When ``correlation_id`` is not passed explicitly, ``build_event`` falls back to
the current request id from ``app.core.context`` (set by ``RequestIdMiddleware``).

Delivery is in-process and awaited: every subscriber for the event type is
invoked independently, and a failing subscriber is logged without breaking the
request or the other subscribers (10_Event_Architecture.md #11 Processing).
Duplicate delivery is suppressed by a bounded LRU set of seen eventIds. A dead
letter queue / persistence is out of scope for the MVP (backlog).
"""

import logging
import uuid
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from app.core.context import get_current_request_id

logger = logging.getLogger("devos.events")

EVENT_CONTRACT_VERSION = "1.0"
DEDUP_CAPACITY = 1024

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]

_subscribers: dict[str, list[EventHandler]] = {}
_seen_event_ids: OrderedDict[str, None] = OrderedDict()


def build_event(
    *,
    event_type: str,
    organization_id: uuid.UUID | None,
    aggregate_id: uuid.UUID,
    payload: dict[str, Any],
    source_module: str,
    correlation_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_metadata: dict[str, Any] = {
        "correlationId": (
            correlation_id if correlation_id is not None else get_current_request_id()
        ),
        "sourceModule": source_module,
    }
    if metadata:
        event_metadata.update(metadata)
    return {
        "eventId": f"evt_{uuid.uuid4().hex}",
        "eventType": event_type,
        "version": EVENT_CONTRACT_VERSION,
        "timestamp": datetime.now(UTC).isoformat(),
        "organizationId": str(organization_id) if organization_id is not None else None,
        "aggregateId": str(aggregate_id),
        "payload": payload,
        "metadata": event_metadata,
    }


def subscribe(event_type: str, handler: EventHandler) -> None:
    handlers = _subscribers.setdefault(event_type, [])
    if handler not in handlers:
        handlers.append(handler)


def unsubscribe(event_type: str, handler: EventHandler) -> None:
    handlers = _subscribers.get(event_type, [])
    if handler in handlers:
        handlers.remove(handler)


def _remember_event(event_id: str) -> bool:
    """Return True if this event id is new; False if already seen."""
    if event_id in _seen_event_ids:
        _seen_event_ids.move_to_end(event_id)
        return False
    _seen_event_ids[event_id] = None
    if len(_seen_event_ids) > DEDUP_CAPACITY:
        _seen_event_ids.popitem(last=False)
    return True


async def publish_event(event: dict[str, Any]) -> None:
    event_id = event.get("eventId")
    if isinstance(event_id, str) and not _remember_event(event_id):
        return
    event_type = event.get("eventType")
    handlers = list(_subscribers.get(event_type, [])) if isinstance(event_type, str) else []
    for handler in handlers:
        try:
            await handler(event)
        except Exception:  # noqa: BLE001 - one subscriber must not break others
            logger.exception(
                "Event handler failed for eventType=%s eventId=%s",
                event_type,
                event_id,
            )
