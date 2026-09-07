"""Task domain event contracts (10_Event_Architecture.md, MVP Task Events).

Events are published through the real in-process dispatcher in
``app.core.events`` after the business transaction has committed.
"""

from app.core.events import build_event, publish_event
from app.modules.tasks.models import Task

SOURCE_MODULE = "Tasks"


def _task_payload(task: Task) -> dict[str, object]:
    return {
        "taskId": str(task.id),
        "projectId": str(task.project_id),
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "assigneeId": str(task.assignee_id) if task.assignee_id is not None else None,
        "dueDate": task.due_date.isoformat() if task.due_date is not None else None,
    }


async def publish_task_created(task: Task) -> None:
    await publish_event(
        build_event(
            event_type="TaskCreated",
            organization_id=task.organization_id,
            aggregate_id=task.id,
            payload=_task_payload(task),
            source_module=SOURCE_MODULE,
        ),
    )


async def publish_task_assigned(task: Task) -> None:
    await publish_event(
        build_event(
            event_type="TaskAssigned",
            organization_id=task.organization_id,
            aggregate_id=task.id,
            payload={
                "taskId": str(task.id),
                "projectId": str(task.project_id),
                "taskTitle": task.title,
                "assigneeId": str(task.assignee_id) if task.assignee_id is not None else None,
            },
            source_module=SOURCE_MODULE,
        ),
    )


async def publish_task_completed(task: Task) -> None:
    await publish_event(
        build_event(
            event_type="TaskCompleted",
            organization_id=task.organization_id,
            aggregate_id=task.id,
            payload={
                "taskId": str(task.id),
                "projectId": str(task.project_id),
                "assigneeId": str(task.assignee_id) if task.assignee_id is not None else None,
                "completedAt": task.updated_at.isoformat(),
            },
            source_module=SOURCE_MODULE,
        ),
    )
