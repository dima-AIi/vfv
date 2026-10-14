"""OpenAI-compatible chat completions provider.

Works with any OpenAI-compatible endpoint (Groq, NVIDIA build, Google Gemini
openai-endpoint, OpenRouter, local Ollama). Fully env-driven via
``AI_BASE_URL`` / ``AI_API_KEY`` / ``AI_MODEL`` / ``AI_TIMEOUT_SECONDS``.

Security rules enforced here:
* the API key is only ever sent as a ``Bearer`` header — it never appears in
  log records or in ``AppError`` messages;
* upstream error bodies are never echoed into error messages.
"""

import logging
from typing import Any

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.modules.ai.provider import AIRequest, AIResponse

logger = logging.getLogger("devos.ai.openai_compatible")

TEMPERATURE = 0.3
SUMMARY_MAX_CHARS = 200

SYSTEM_PROMPTS: dict[str, str] = {
    "analyze": (
        "Ты — аналитик бизнес-процессов платформы DevOS. Проанализируй запрос "
        "и подключённый контекст: выдели ключевое, отметь риски и пробелы. "
        "Отвечай на русском языке в markdown."
    ),
    "plan": (
        "Ты — планировщик задач платформы DevOS. Составь пошаговый план "
        "выполнения запроса с учётом контекста: нумерованные шаги, каждый "
        "проверяем. Отвечай на русском языке в markdown."
    ),
    "execute": (
        "Ты — исполнитель платформы DevOS. Сформулируй результат выполнения "
        "запрошенного действия по имеющемуся контексту. Отвечай на русском "
        "языке в markdown."
    ),
    "summarize": (
        "Ты — редактор платформы DevOS. Сожми запрос и контекст в 3–5 пунктов. "
        "Отвечай на русском языке в markdown."
    ),
}


class OpenAICompatibleProvider:
    """Calls ``POST {AI_BASE_URL}/chat/completions`` (OpenAI chat format)."""

    name = "openai_compatible"

    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._transport = transport

    async def analyze(self, request: AIRequest) -> AIResponse:
        return await self._chat("analyze", request)

    async def plan(self, request: AIRequest) -> AIResponse:
        return await self._chat("plan", request)

    async def execute(self, request: AIRequest) -> AIResponse:
        return await self._chat("execute", request)

    async def summarize(self, request: AIRequest) -> AIResponse:
        return await self._chat("summarize", request)

    def _require_config(self) -> tuple[str, str, str]:
        base_url = self._settings.ai_base_url.strip()
        api_key = self._settings.ai_api_key.strip()
        model = self._settings.ai_model.strip()
        missing = [
            name
            for name, value in (
                ("AI_BASE_URL", base_url),
                ("AI_API_KEY", api_key),
                ("AI_MODEL", model),
            )
            if not value
        ]
        if missing:
            raise AppError(
                "OpenAI-совместимый провайдер не настроен: не заданы "
                + ", ".join(missing)
                + ".",
                code="AI_PROVIDER_NOT_CONFIGURED",
                status_code=400,
            )
        return base_url, api_key, model

    async def _chat(self, action_type: str, request: AIRequest) -> AIResponse:
        base_url, api_key, model = self._require_config()
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPTS[action_type]},
                {"role": "user", "content": self._user_prompt(request)},
            ],
            "temperature": TEMPERATURE,
        }
        url = base_url.rstrip("/") + "/chat/completions"
        try:
            async with httpx.AsyncClient(
                timeout=self._settings.ai_timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            logger.warning("AI provider request timed out: url=%s", url)
            raise AppError(
                "Превышено время ожидания ответа AI-провайдера.",
                code="AI_PROVIDER_TIMEOUT",
                status_code=504,
            ) from exc
        except httpx.HTTPError as exc:
            logger.warning("AI provider request failed: %s", type(exc).__name__)
            raise AppError(
                "AI-провайдер недоступен.",
                code="AI_PROVIDER_FAILED",
                status_code=502,
            ) from exc
        if response.status_code // 100 != 2:
            logger.warning("AI provider returned HTTP %s", response.status_code)
            raise AppError(
                f"AI-провайдер вернул ошибку: HTTP {response.status_code}.",
                code="AI_PROVIDER_FAILED",
                status_code=502,
            )
        return self._parse_response(response)

    @staticmethod
    def _parse_response(response: httpx.Response) -> AIResponse:
        try:
            body = response.json()
            content = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("AI provider returned malformed body: %s", type(exc).__name__)
            raise AppError(
                "AI-провайдер вернул некорректный ответ.",
                code="AI_PROVIDER_FAILED",
                status_code=502,
            ) from exc
        if not isinstance(content, str) or not content.strip():
            raise AppError(
                "AI-провайдер вернул пустой ответ.",
                code="AI_PROVIDER_FAILED",
                status_code=502,
            )
        text = content.strip()
        return AIResponse(content=text, summary=text.splitlines()[0][:SUMMARY_MAX_CHARS])

    @staticmethod
    def _user_prompt(request: AIRequest) -> str:
        parts: list[str] = []
        if request.project_name:
            parts.append(f"Проект: {request.project_name}")
        if request.task_title:
            parts.append(f"Задача: {request.task_title}")
        if request.context_text:
            parts.append(f"Контекст:\n{request.context_text}")
        parts.append(f"Запрос:\n{request.input_text.strip()}")
        return "\n\n".join(parts)
