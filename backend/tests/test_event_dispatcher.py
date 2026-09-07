import asyncio
import uuid
from typing import Any

from app.core.events import build_event, publish_event, subscribe, unsubscribe


def _event(event_type: str) -> dict[str, Any]:
    return build_event(
        event_type=event_type,
        organization_id=None,
        aggregate_id=uuid.uuid4(),
        payload={"x": 1},
        source_module="Test",
    )


def test_dispatcher_delivers_and_dedups_by_event_id() -> None:
    received: list[dict[str, Any]] = []

    async def handler(event: dict[str, Any]) -> None:
        received.append(event)

    subscribe("DispatcherDedupTest", handler)
    try:
        event = _event("DispatcherDedupTest")

        async def run() -> None:
            await publish_event(event)
            await publish_event(event)  # same eventId -> delivered once

        asyncio.run(run())
        assert len(received) == 1
        assert received[0]["metadata"]["sourceModule"] == "Test"
        assert "correlationId" in received[0]["metadata"]
    finally:
        unsubscribe("DispatcherDedupTest", handler)


def test_failing_handler_does_not_break_others() -> None:
    calls: list[str] = []

    async def bad(event: dict[str, Any]) -> None:
        calls.append("bad")
        raise RuntimeError("boom")

    async def good(event: dict[str, Any]) -> None:
        calls.append("good")

    subscribe("DispatcherErrorTest", bad)
    subscribe("DispatcherErrorTest", good)
    try:
        asyncio.run(publish_event(_event("DispatcherErrorTest")))
        assert calls == ["bad", "good"]
    finally:
        unsubscribe("DispatcherErrorTest", bad)
        unsubscribe("DispatcherErrorTest", good)
