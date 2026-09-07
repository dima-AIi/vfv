from app.core.config import settings
from app.core.errors import AppError
from app.modules.ai.mock_provider import MockAIProvider
from app.modules.ai.provider import AIProvider

_PROVIDERS: dict[str, AIProvider] = {
    MockAIProvider.name: MockAIProvider(),
}


def get_provider(name: str | None = None) -> AIProvider:
    provider_name = name or settings.ai_provider
    provider = _PROVIDERS.get(provider_name)
    if provider is None:
        raise AppError(
            f"Неизвестный AI-провайдер: {provider_name}",
            code="AI_PROVIDER_NOT_FOUND",
            status_code=400,
        )
    return provider


def registered_providers() -> list[str]:
    return sorted(_PROVIDERS)
