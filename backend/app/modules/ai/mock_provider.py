import re

from app.modules.ai.provider import AIRequest, AIResponse

_ACTION_TITLES = {
    "analyze": "Анализ",
    "plan": "План работ",
    "execute": "Результат выполнения",
    "summarize": "Сводка",
}

_STOP_WORDS = frozenset(
    {
        "и",
        "в",
        "на",
        "с",
        "для",
        "по",
        "как",
        "что",
        "the",
        "a",
        "an",
        "to",
        "of",
        "for",
        "and",
        "in",
        "on",
        "with",
    },
)


def _keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[\w][\w\-]{2,}", text.lower())
    seen: list[str] = []
    for word in words:
        if word not in _STOP_WORDS and word not in seen:
            seen.append(word)
        if len(seen) >= limit:
            break
    return seen


class MockAIProvider:
    """Deterministic offline provider used for the DevOS MVP prototype.

    Produces structured heuristic responses without external calls.
    """

    name = "mock"

    async def analyze(self, request: AIRequest) -> AIResponse:
        keywords = _keywords(request.input_text)
        context_note = self._context_note(request)
        lines = [
            f"# {_ACTION_TITLES['analyze']}",
            "",
            f"**Запрос:** {request.input_text.strip()}",
            "",
            "## Ключевые темы",
            "",
        ]
        if keywords:
            lines.extend(f"- {word}" for word in keywords)
        else:
            lines.append("- явные ключевые темы не выделены")
        lines.extend(
            [
                "",
                "## Наблюдения",
                "",
                "1. Запрос касается рабочей области проекта"
                + (f" «{request.project_name}»" if request.project_name else "") + ".",
                "2. Контекст документации "
                + (
                    f"подключён ({len(context_note.split())} слов)."
                    if context_note
                    else "не подключён."
                ),
                "3. Для перехода к реализации рекомендуется сформировать план (action: plan).",
            ],
        )
        return AIResponse(content="\n".join(lines), summary=self._summary("analyze", keywords))

    async def plan(self, request: AIRequest) -> AIResponse:
        keywords = _keywords(request.input_text, limit=5)
        subject = ", ".join(keywords) if keywords else "поставленная задача"
        steps = [
            "Уточнить цель и критерии готовности",
            f"Подготовить контекст по теме: {subject}",
            "Реализовать минимальное изменение",
            "Проверить результат тестами",
            "Обновить документацию при изменении поведения",
        ]
        lines = [
            f"# {_ACTION_TITLES['plan']}",
            "",
            f"**Задача:** {request.input_text.strip()}",
            "",
        ]
        lines.extend(f"{i}. {step}" for i, step in enumerate(steps, start=1))
        lines.extend(
            [
                "",
                "> План сформирован mock-провайдером и требует подтверждения человека.",
            ],
        )
        return AIResponse(content="\n".join(lines), summary=self._summary("plan", keywords))

    async def execute(self, request: AIRequest) -> AIResponse:
        keywords = _keywords(request.input_text)
        focus = keywords[0] if keywords else "запрошенное действие"
        lines = [
            f"# {_ACTION_TITLES['execute']}",
            "",
            f"Выполнено концептуальное действие над «{focus}».",
            "",
            "**Входные данные:**",
            "",
            request.input_text.strip(),
            "",
            "**Ожидаемый эффект:** изменения зафиксированы в протоколе действия; "
            "реальные side-effect операции в MVP-прототипе отключены.",
        ]
        return AIResponse(content="\n".join(lines), summary=self._summary("execute", keywords))

    async def summarize(self, request: AIRequest) -> AIResponse:
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", request.input_text) if s.strip()]
        top = sentences[:3]
        lines = [
            f"# {_ACTION_TITLES['summarize']}",
            "",
            "**Краткое содержание:**",
            "",
        ]
        lines.extend(f"- {sentence}" for sentence in top) if top else lines.append("- пусто")
        if request.context_text:
            lines.extend(
                [
                    "",
                    f"_Учтён контекст объёмом {len(request.context_text.split())} слов._",
                ],
            )
        return AIResponse(content="\n".join(lines), summary=self._summary("summarize", []))

    @staticmethod
    def _context_note(request: AIRequest) -> str:
        return request.context_text or ""

    @staticmethod
    def _summary(action_type: str, keywords: list[str]) -> str:
        base = f"{_ACTION_TITLES.get(action_type, action_type)} выполнен (mock)."
        if keywords:
            return f"{base} Темы: {', '.join(keywords[:4])}."
        return base
