import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

REGISTER_PAYLOAD = {
    "email": "Alice@Example.com",
    "password": "correct-horse-battery",
    "displayName": "Alice",
}


def _register(client: TestClient, **overrides: str) -> dict:
    payload = {**REGISTER_PAYLOAD, **overrides}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def _login(client: TestClient, email: str = REGISTER_PAYLOAD["email"],
           password: str = REGISTER_PAYLOAD["password"]) -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _auth_header(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def test_full_auth_cycle(client: TestClient) -> None:
    user = _register(client)
    assert user["email"] == REGISTER_PAYLOAD["email"].lower()
    assert user["status"] == "active"

    auth = _login(client)
    tokens = auth["tokens"]
    assert tokens["token_type"] == "bearer"
    assert auth["user"]["id"] == user["id"]
    assert "password_hash" not in __import__("json").dumps(auth)

    me = client.get("/api/v1/auth/me", headers=_auth_header(tokens))
    assert me.status_code == 200
    assert me.json()["data"]["email"] == user["email"]

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()["data"]["tokens"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    reuse = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": tokens["refresh_token"]},
    )
    assert reuse.status_code == 401
    assert reuse.json()["error"]["code"] == "SESSION_REVOKED"

    logout = client.post("/api/v1/auth/logout", headers=_auth_header(new_tokens))
    assert logout.status_code == 204

    me_after_logout = client.get("/api/v1/auth/me", headers=_auth_header(new_tokens))
    assert me_after_logout.status_code == 200


def test_login_with_wrong_password_401_uniform(client: TestClient) -> None:
    _register(client)
    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever-long"},
    )
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrong-password-1"},
    )
    assert unknown.status_code == wrong_password.status_code == 401
    assert unknown.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
    assert wrong_password.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


def test_duplicate_email_409(client: TestClient) -> None:
    _register(client)
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": REGISTER_PAYLOAD["email"].upper(),
            "password": "another-pass-123",
            "displayName": "Clone",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_weak_password_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "weak@example.com", "password": "short", "displayName": "W"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PASSWORD_TOO_WEAK"


def test_blocked_user_403_on_login_and_me(client: TestClient) -> None:
    _register(client)
    tokens = _login(client)["tokens"]

    async def block_user() -> None:
        from app.core.database import engine

        async with engine.begin() as connection:
            await connection.execute(
                text("UPDATE user SET status = 'blocked' WHERE email = :email"),
                {"email": REGISTER_PAYLOAD["email"].lower()},
            )

    import asyncio

    asyncio.run(block_user())

    login_blocked = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
    )
    assert login_blocked.status_code == 403
    assert login_blocked.json()["error"]["code"] == "USER_BLOCKED"

    me_blocked = client.get("/api/v1/auth/me", headers=_auth_header(tokens))
    assert me_blocked.status_code == 403
    assert me_blocked.json()["error"]["code"] == "USER_BLOCKED"


def test_expired_access_token_401(client: TestClient) -> None:
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from app.core.config import settings

    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "expired@example.com",
        "type": "access",
        "iat": int(now.timestamp()) - 3600,
        "exp": int((now - timedelta(seconds=30)).timestamp()),
    }
    expired = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "EXPIRED_TOKEN"


def test_tampered_access_token_401(client: TestClient) -> None:
    _register(client)
    tokens = _login(client)["tokens"]
    token = tokens["access_token"]
    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] in {"INVALID_TOKEN", "EXPIRED_TOKEN"}


def test_unknown_refresh_token_401(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": "totally-unknown-refresh-token-value"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_REFRESH_TOKEN"


def test_no_password_hash_in_any_identity_response(client: TestClient) -> None:
    _register(client)
    for response in (
        client.post(
            "/api/v1/auth/login",
            json={"email": REGISTER_PAYLOAD["email"], "password": REGISTER_PAYLOAD["password"]},
        ),
        client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": "x" * 32},
        ),
    ):
        body = response.text
        assert "password_hash" not in body


def test_audit_records_written(client: TestClient) -> None:
    _register(client)
    _login(client)
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": REGISTER_PAYLOAD["email"], "password": "wrong-password-1"},
    )
    assert bad_login.status_code == 401
    tokens = _login(client)["tokens"]
    client.post("/api/v1/auth/logout", headers=_auth_header(tokens))

    async def fetch_actions() -> list[tuple[str, str]]:
        from app.core.database import engine

        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT action_type, detail FROM audit_record ORDER BY created_at"),
            )
            return [(row[0], row[1]) for row in result.all()]

    import asyncio

    actions = asyncio.run(fetch_actions())
    recorded = [action for action, _detail in actions]
    for expected in ("USER_REGISTERED", "LOGIN_SUCCESS", "LOGIN_FAILED", "LOGOUT"):
        assert expected in recorded, (expected, actions)

    joined = " ".join(detail for _action, detail in actions).lower()
    assert REGISTER_PAYLOAD["password"].lower() not in joined
