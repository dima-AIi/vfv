from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


def _owner(client: TestClient, email: str) -> AuthorizedClient:
    headers = auth_headers(client, email, create_org=True, org_name=f"SetOrg-{email}")
    return AuthorizedClient(client, headers)


def test_organization_settings_write_read(client: TestClient) -> None:
    owned = _owner(client, "set.org@example.com")
    put = owned.put(
        "/api/v1/settings",
        json={"scope": "organization", "key": "theme", "value": '"dark"'},
    )
    assert put.status_code == 200, put.text
    listed = owned.get("/api/v1/settings", params={"scope": "organization"}).json()["data"]
    assert {"key": "theme", "value": '"dark"'} in listed


def test_org_admin_cannot_write_platform(client: TestClient) -> None:
    owned = _owner(client, "set.plat@example.com")
    response = owned.put(
        "/api/v1/settings",
        json={"scope": "platform", "key": "signup", "value": "true"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_user_settings_own_scope(client: TestClient) -> None:
    owned = _owner(client, "set.user@example.com")
    put = owned.put(
        "/api/v1/settings",
        json={"scope": "user", "key": "locale", "value": '"ru"'},
    )
    assert put.status_code == 200
    listed = owned.get("/api/v1/settings", params={"scope": "user"}).json()["data"]
    assert {"key": "locale", "value": '"ru"'} in listed


def test_invalid_setting_key(client: TestClient) -> None:
    owned = _owner(client, "set.key@example.com")
    response = owned.put(
        "/api/v1/settings",
        json={"scope": "user", "key": "BAD KEY!", "value": "1"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_SETTING_KEY"


def test_invalid_setting_value(client: TestClient) -> None:
    owned = _owner(client, "set.val@example.com")
    response = owned.put(
        "/api/v1/settings",
        json={"scope": "user", "key": "x", "value": "not-json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_SETTING_VALUE"


def test_settings_upsert_overwrites(client: TestClient) -> None:
    owned = _owner(client, "set.upsert@example.com")
    owned.put("/api/v1/settings", json={"scope": "user", "key": "k", "value": "1"})
    owned.put("/api/v1/settings", json={"scope": "user", "key": "k", "value": "2"})
    listed = owned.get("/api/v1/settings", params={"scope": "user"}).json()["data"]
    matches = [s for s in listed if s["key"] == "k"]
    assert len(matches) == 1
    assert matches[0]["value"] == "2"
