"""Notification subscribers for domain events (10_Event_Architecture.md).

Each handler runs in its own database session so that subscriber work is
isolated from the publishing transaction and from other subscribers. Handlers
only read the event payload (public ids/titles), never secrets.
"""

import uuid
from typing import Any

from app.core.database import session_factory
from app.core.events import subscribe
from app.modules.notifications.service import NotificationService


def _as_uuid(value: Any) -> uuid.UUID | None:
    if not isinstance(value, str):
        return None
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _org_id(event: dict[str, Any]) -> uuid.UUID | None:
    return _as_uuid(event.get("organizationId"))


async def handle_task_assigned(event: dict[str, Any]) -> None:
    payload = event.get("payload", {})
    assignee_id = _as_uuid(payload.get("assigneeId"))
    if assignee_id is None:
        return
    task_title = str(payload.get("taskTitle", ""))
    task_id = _as_uuid(payload.get("taskId"))
    async with session_factory() as session:
        await NotificationService(session).create(
            user_id=assignee_id,
            organization_id=_org_id(event),
            title="Вам назначена задача",
            body=f"Вам назначена задача «{task_title}».",
            entity_type="task",
            entity_id=task_id,
        )


async def handle_comment_created(event: dict[str, Any]) -> None:
    payload = event.get("payload", {})
    assignee_id = _as_uuid(payload.get("taskAssigneeId"))
    author_id = _as_uuid(payload.get("authorId"))
    if assignee_id is None or assignee_id == author_id:
        return
    task_id = _as_uuid(payload.get("taskId"))
    excerpt = str(payload.get("excerpt", ""))
    async with session_factory() as session:
        await NotificationService(session).create(
            user_id=assignee_id,
            organization_id=_org_id(event),
            title="Новый комментарий к задаче",
            body=f"К вашей задаче оставлен комментарий: {excerpt}",
            entity_type="comment",
            entity_id=task_id,
        )


def register_notification_subscribers() -> None:
    subscribe("TaskAssigned", handle_task_assigned)
    subscribe("CommentCreated", handle_comment_created)
