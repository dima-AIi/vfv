"""Comment domain event contract (10_Event_Architecture.md naming rules).

Published after a comment is committed. Payload carries the task assignee so
subscribers (notifications) can route without extra queries.
"""

from app.core.events import build_event, publish_event
from app.modules.comments.models import Comment
from app.modules.tasks.models import Task

SOURCE_MODULE = "Comments"
EXCERPT_LIMIT = 200


async def publish_comment_created(comment: Comment, task: Task) -> None:
    await publish_event(
        build_event(
            event_type="CommentCreated",
            organization_id=comment.organization_id,
            aggregate_id=comment.id,
            payload={
                "commentId": str(comment.id),
                "taskId": str(task.id),
                "projectId": str(task.project_id),
                "authorId": str(comment.author_id) if comment.author_id is not None else None,
                "taskAssigneeId": (
                    str(task.assignee_id) if task.assignee_id is not None else None
                ),
                "excerpt": comment.body[:EXCERPT_LIMIT],
            },
            source_module=SOURCE_MODULE,
        ),
    )
