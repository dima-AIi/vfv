import pytest

from app.core.config import DEV_DEFAULT_SECRET_KEY, Settings


def test_default_secret_rejected_outside_local() -> None:
    with pytest.raises(RuntimeError, match="SECRET_KEY must be set via environment"):
        Settings(app_env="production", secret_key=DEV_DEFAULT_SECRET_KEY)


def test_default_secret_allowed_in_local() -> None:
    settings = Settings(app_env="local", secret_key=DEV_DEFAULT_SECRET_KEY)
    assert settings.secret_key == DEV_DEFAULT_SECRET_KEY


def test_custom_secret_allowed_outside_local() -> None:
    settings = Settings(app_env="production", secret_key="a-real-production-secret")
    assert settings.secret_key == "a-real-production-secret"
