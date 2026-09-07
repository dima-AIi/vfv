"""Authorization helper for API tests: register, login, optionally create org."""

import uuid

from fastapi.testclient import TestClient
from httpx import Response

DEFAULT_PASSWORD = "strong-password-123"


class AuthorizedClient:
    """Wraps TestClient, injecting Bearer headers on every request."""

    def __init__(self, base: TestClient, headers: dict[str, str]) -> None:
        self._base = base
        self._headers = headers

    def get(self, url: str, **kwargs: object) -> Response:
        kwargs["headers"] = {**self._headers, **kwargs.pop("headers", {})}
        return self._base.get(url, **kwargs)

    def post(self, url: str, **kwargs: object) -> Response:
        kwargs["headers"] = {**self._headers, **kwargs.pop("headers", {})}
        return self._base.post(url, **kwargs)

    def patch(self, url: str, **kwargs: object) -> Response:
        kwargs["headers"] = {**self._headers, **kwargs.pop("headers", {})}
        return self._base.patch(url, **kwargs)

    def put(self, url: str, **kwargs: object) -> Response:
        kwargs["headers"] = {**self._headers, **kwargs.pop("headers", {})}
        return self._base.put(url, **kwargs)

    def delete(self, url: str, **kwargs: object) -> Response:
        kwargs["headers"] = {**self._headers, **kwargs.pop("headers", {})}
        return self._base.delete(url, **kwargs)


def _unique_email(base: str) -> str:
    """Generate unique email using UUID to avoid conflicts across test runs."""
    return f"{base.split('@')[0]}+{uuid.uuid4().hex[:8]}@{base.split('@')[1]}"


def _unique_org_name(base: str) -> str:
    """Generate unique org name using UUID to avoid conflicts."""
    return f"{base}-{uuid.uuid4().hex[:8]}"


def auth_headers(
    client: TestClient,
    base_email: str,
    password: str = DEFAULT_PASSWORD,
    display_name: str | None = None,
    create_org: bool = False,
    org_name: str | None = None,
) -> dict[str, str]:
    """Register user, login, return Bearer headers; optionally create organization."""
    email = _unique_email(base_email)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "displayName": display_name or base_email.split("@")[0],
        },
    )
    assert response.status_code == 201, response.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    header = {"Authorization": f"Bearer {login.json()['data']['tokens']['access_token']}"}

    if create_org:
        org = client.post(
            "/api/v1/organizations",
            json={"name": _unique_org_name(org_name or f"Org-{base_email}")},
            headers=header,
        )
        assert org.status_code == 201, org.text

    return header