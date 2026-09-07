"""Seed the DevOS MVP database with demo data.

Usage:
    cd backend
    uv run alembic upgrade head   # if not done yet
    uv run python ../scripts/seed_demo.py
"""

import asyncio

from sqlalchemy import select

import app.modules.ai.models  # noqa: F401
import app.modules.documents.models  # noqa: F401
import app.modules.projects.models  # noqa: F401
import app.modules.tasks.models  # noqa: F401
from app.core.database import (
    Base,  # noqa: F401  (ensures models are registered)
    session_factory,
)
from app.core.models import utcnow
from app.modules.ai.models import AIAction, AIResult
from app.modules.documents.models import Document
from app.modules.projects.models import Project
from app.modules.tasks.models import Task

DEMO_PROJECT_NAME = "DevOS Onboarding"

DOCS = [
    (
        "Architecture Rules",
        "01_ARCHITECTURE/05A_Architecture_Rules.md",
        "architecture",
    ),
    (
        "MVP Specification",
        "02_PRODUCT/13_MVP_Specification.md",
        "product",
    ),
    (
        "Project Initialization",
        "03_DEVELOPMENT/17_Project_Initialization.md",
        "development",
    ),
]


async def main() -> None:
    async with session_factory() as session:
        existing = await session.scalar(
            select(Project).where(Project.name == DEMO_PROJECT_NAME),
        )
        if existing is not None:
            print("Demo project already present, nothing to do.")
            return

        project = Project(
            name=DEMO_PROJECT_NAME,
            description=(
                "Демонстрационный проект: знакомство с рабочим пространством, "
                "документационным контекстом и AI-ассистентом DevOS."
            ),
        )
        session.add(project)
        await session.flush()

        task_open = Task(
            project_id=project.id,
            title="Изучить архитектурные правила DevOS",
            description="Открыть 05A_Architecture_Rules и зафиксировать ключевые инварианты.",
            status="open",
            priority="high",
        )
        task_progress = Task(
            project_id=project.id,
            title="Подключить документацию как контекст",
            description="Добавить документы проекта во вкладке Documentation.",
            status="in_progress",
            priority="medium",
        )
        session.add_all([task_open, task_progress])
        await session.flush()

        for title, path, category in DOCS:
            session.add(
                Document(
                    project_id=project.id,
                    title=title,
                    category=category,
                    relative_path=path,
                ),
            )

        action = AIAction(
            project_id=project.id,
            task_id=task_progress.id,
            action_type="analyze",
            input_text="Проанализировать, с чего начать знакомство с платформой DevOS.",
            context_summary=f"project={project.name}",
            status="completed",
            provider="mock",
            created_at=utcnow(),
            completed_at=utcnow(),
        )
        session.add(action)
        await session.flush()
        session.add(
            AIResult(
                action_id=action.id,
                content=(
                    "# Анализ\n\n"
                    "**Запрос:** Проанализировать, с чего начать знакомство с платформой DevOS.\n\n"
                    "## Рекомендованные шаги\n\n"
                    "1. Открыть вкладку Documentation и прочитать Architecture Rules.\n"
                    "2. Просмотреть MVP Specification, чтобы понять границы первой версии.\n"
                    "3. Запустить AI-действие plan для формирования собственного плана.\n"
                ),
                summary="Анализ выполнен (mock). Темы: devos, архитектура, mvp.",
                created_at=utcnow(),
            ),
        )

        await session.commit()
        print(f"Demo data seeded: project '{DEMO_PROJECT_NAME}'.")


if __name__ == "__main__":
    asyncio.run(main())
