from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]

DEV_DEFAULT_SECRET_KEY = "insecure-dev-only-secret"

DEFAULT_DOCUMENT_ROOTS: tuple[str, ...] = (
    "00_RESEARCH",
    "01_ARCHITECTURE",
    "02_PRODUCT",
    "03_DEVELOPMENT",
    "04_PROJECT",
    "99_AI",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DevOS"
    app_env: str = "local"
    app_version: str = "0.1.0"

    secret_key: str = DEV_DEFAULT_SECRET_KEY
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database_url: str = f"sqlite+aiosqlite:///{REPO_ROOT / 'devos.db'}"

    ai_provider: str = "mock"
    anthropic_api_key: str = ""

    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @model_validator(mode="after")
    def _reject_default_secret_outside_local(self) -> "Settings":
        if self.app_env != "local" and self.secret_key == DEV_DEFAULT_SECRET_KEY:
            raise RuntimeError("SECRET_KEY must be set via environment")
        return self

    document_roots: list[str] = list(DEFAULT_DOCUMENT_ROOTS)
    document_max_bytes: int = 512_000

    storage_dir: Path = REPO_ROOT / "storage"
    file_max_bytes: int = 25_000_000

    @property
    def resolved_document_roots(self) -> list[Path]:
        roots: list[Path] = []
        for raw in self.document_roots:
            path = Path(raw)
            if not path.is_absolute():
                path = REPO_ROOT / path
            roots.append(path.resolve())
        return roots


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
