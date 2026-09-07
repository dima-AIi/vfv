import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.errors import AppError

ALGORITHM = "HS256"
REFRESH_TOKEN_BYTES = 48

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return cast("str", pwd_context.hash(password))


def verify_password(password: str, password_hash: str) -> bool:
    return cast("bool", pwd_context.verify(password, password_hash))


def create_access_token(
    *,
    user_id: uuid.UUID,
    email: str,
    session_id: uuid.UUID | None = None,
) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    if session_id is not None:
        payload["sid"] = str(session_id)
    return cast("str", jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM))


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
    except ExpiredSignatureError as exc:
        raise AppError(
            "Срок действия токена истёк.", code="EXPIRED_TOKEN", status_code=401
        ) from exc
    except JWTError as exc:
        raise AppError("Недействительный токен.", code="INVALID_TOKEN", status_code=401) from exc
    if payload.get("type") != "access":
        raise AppError("Недопустимый тип токена.", code="INVALID_TOKEN", status_code=401)
    return payload


def generate_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(REFRESH_TOKEN_BYTES)
    return token, hash_refresh_token(token)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
