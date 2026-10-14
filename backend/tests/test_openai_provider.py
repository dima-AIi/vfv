import json
from typing import Any

import httpx
import pytest

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.modules.ai.mock_provider import MockAIProvider
from app.modules.ai.openai_provider import SYSTEM_PROMPTS, OpenAICompatibleProvider
from app.modules.ai.provider import AIRequest
from app.modules.ai.registry import get_provider, registered_providers

API_KEY = "sk-test-super-secret"


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = {
        "app_env": "local",
        "ai_base_url": "https://ai.test/v1",
        "ai_api_key": API_KEY,
        "ai_model": "test-model",
        "ai_timeout_seconds": 5.0,
    }
    base.update(overrides)
    return Settings(**base)


def _request() -> AIRequest:
    return AIRequest(
        action_type="plan",
        input_text="Запустить демо MVP",
        context_text="Контекст проекта",
        project_name="P1",
        task_title="T1",
    )


def _completion_body(text: str) -> dict[str, Any]:
    return {"choices": [{"message": {"role": "assistant", "content": text}}]}


def _provider(handler: Any) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(settings=_settings(), transport=httpx.MockTransport(handler))


async def test_request_uses_bearer_model_and_russian_system_prompt() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=_completion_body("# План\n\n1. Шаг"))

    response = await _provider(handler).plan(_request())

    assert response.content == "# План\n\n1. Шаг"
    assert captured["url"] == "https://ai.test/v1/chat/completions"
    assert captured["auth"] == f"Bearer {API_KEY}"
    body = captured["body"]
    assert body["model"] == "test-model"
    assert body["temperature"] == 0.3
    messages = body["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == SYSTEM_PROMPTS["plan"]
    assert "Запустить демо MVP" in messages[1]["content"]
    assert "Контекст проекта" in messages[1]["content"]


async def test_success_parses_content_and_summary() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_completion_body("Первая строка\n\nОстальной текст"))

    response = await _provider(handler).analyze(_request())
    assert response.content == "Первая строка\n\nОстальной текст"
    assert response.summary == "Первая строка"


async def test_summary_is_capped_at_200_chars() -> None:
    long_line = "а" * 500

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_completion_body(long_line))

    response = await _provider(handler).summarize(_request())
    assert response.summary == "а" * 200


async def test_trailing_slash_in_base_url_is_normalized() -> None:
    captured_urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_urls.append(str(request.url))
        return httpx.Response(200, json=_completion_body("ok"))

    provider = OpenAICompatibleProvider(
        settings=_settings(ai_base_url="https://ai.test/v1/"),
        transport=httpx.MockTransport(handler),
    )
    await provider.execute(_request())
    assert captured_urls == ["https://ai.test/v1/chat/completions"]


async def test_http_error_maps_to_failed_without_key_or_body_leak() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": f"invalid key {API_KEY}"}})

    with pytest.raises(AppError) as excinfo:
        await _provider(handler).analyze(_request())

    error = excinfo.value
    assert error.code == "AI_PROVIDER_FAILED"
    assert error.status_code == 502
    assert API_KEY not in error.message
    assert API_KEY not in str(error.details)


async def test_malformed_success_body_maps_to_failed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    with pytest.raises(AppError) as excinfo:
        await _provider(handler).plan(_request())
    assert excinfo.value.code == "AI_PROVIDER_FAILED"
    assert excinfo.value.status_code == 502


async def test_timeout_maps_to_provider_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    with pytest.raises(AppError) as excinfo:
        await _provider(handler).plan(_request())

    assert excinfo.value.code == "AI_PROVIDER_TIMEOUT"
    assert excinfo.value.status_code == 504
    assert API_KEY not in excinfo.value.message


async def test_missing_config_raises_not_configured() -> None:
    provider = OpenAICompatibleProvider(
        settings=_settings(ai_base_url="", ai_api_key="", ai_model=""),
        transport=httpx.MockTransport(lambda request: httpx.Response(200)),
    )
    with pytest.raises(AppError) as excinfo:
        await provider.summarize(_request())

    error = excinfo.value
    assert error.code == "AI_PROVIDER_NOT_CONFIGURED"
    assert error.status_code == 400
    assert "AI_BASE_URL" in error.message
    assert "AI_API_KEY" in error.message
    assert "AI_MODEL" in error.message


def test_mock_remains_default_provider() -> None:
    assert get_settings().ai_provider == "mock"
    assert isinstance(get_provider(), MockAIProvider)


def test_registry_exposes_openai_compatible() -> None:
    assert "openai_compatible" in registered_providers()
    assert isinstance(get_provider("openai_compatible"), OpenAICompatibleProvider)
