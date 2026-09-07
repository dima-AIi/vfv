import hashlib
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.modules.rbac.seed import stable_id
from tests.auth_helper import AuthorizedClient, auth_headers

TEST_DB_PATH = Path(__file__).parent / "_test.db"
TEXT_BYTES = b"hello files module\nsecond line"


def _owner(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"FilesOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _invite(
    client: TestClient,
    owned: AuthorizedClient,
    org_id: str,
    email: str,
    display: str,
) -> tuple[AuthorizedClient, str]:
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": email, "displayName": display},
    ).json()["data"]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": invited["generated_password"]},
    ).json()["data"]["tokens"]["access_token"]
    return AuthorizedClient(client, {"Authorization": f"Bearer {login}"}), invited["id"]


def _make_guest(
    client: TestClient,
    owned: AuthorizedClient,
    org_id: str,
    email: str,
    display: str,
) -> AuthorizedClient:
    member, user_id = _invite(client, owned, org_id, email, display)
    now = datetime.now(UTC).isoformat()
    with sqlite3.connect(TEST_DB_PATH) as connection:
        connection.execute(
            "DELETE FROM user_role WHERE user_id = ? AND organization_id = ?",
            (user_id.replace("-", ""), org_id.replace("-", "")),
        )
        connection.execute(
            "INSERT INTO user_role (id, user_id, role_id, organization_id, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                uuid.uuid4().hex,
                user_id.replace("-", ""),
                stable_id("role", "guest").hex,
                org_id.replace("-", ""),
                now,
                now,
            ),
        )
        connection.commit()
    return member


def _upload(owned: AuthorizedClient, name: str = "notes.txt", data: bytes = TEXT_BYTES):
    return owned.post("/api/v1/files", files={"file": (name, data, "text/plain")})


def test_upload_list_get_download_roundtrip(client: TestClient) -> None:
    owned, _org = _owner(client, "files.rt@example.com")

    created = _upload(owned)
    assert created.status_code == 201, created.text
    meta = created.json()["data"]
    assert meta["filename"] == "notes.txt"
    assert meta["size_bytes"] == len(TEXT_BYTES)
    assert meta["checksum"] == hashlib.sha256(TEXT_BYTES).hexdigest()
    assert meta["current_version"] == 1
    assert "storage_key" not in meta

    file_id = meta["id"]
    listed = owned.get("/api/v1/files").json()["data"]
    assert file_id in {f["id"] for f in listed}

    fetched = owned.get(f"/api/v1/files/{file_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == file_id

    downloaded = owned.get(f"/api/v1/files/{file_id}/content")
    assert downloaded.status_code == 200
    assert downloaded.content == TEXT_BYTES
    assert downloaded.headers["content-disposition"].startswith("attachment")
    assert hashlib.sha256(downloaded.content).hexdigest() == meta["checksum"]


def test_oversize_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    owned, _org = _owner(client, "files.size@example.com")
    monkeypatch.setattr(settings, "file_max_bytes", 5)
    response = _upload(owned, data=b"way too large for the limit")
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"


def test_employee_uploads_guest_denied_upload_but_can_read(client: TestClient) -> None:
    owned, org_id = _owner(client, "files.roles@example.com")
    employee, _ = _invite(client, owned, org_id, "files.emp@example.com", "Emp")
    guest = _make_guest(client, owned, org_id, "files.guest@example.com", "GUEST")

    uploaded = _upload(employee, name="emp.txt", data=b"employee bytes")
    assert uploaded.status_code == 201

    denied = _upload(guest, name="guest.txt", data=b"guest bytes")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    guest_read = guest.get("/api/v1/files")
    assert guest_read.status_code == 200


def test_cross_org_isolation(client: TestClient) -> None:
    owned, _org = _owner(client, "files.a@example.com")
    file_id = _upload(owned).json()["data"]["id"]

    outsider, _ = _owner(client, "files.b@example.com")
    assert outsider.get(f"/api/v1/files/{file_id}").status_code == 404
    assert outsider.get(f"/api/v1/files/{file_id}/content").status_code == 404


def test_versions_flow(client: TestClient) -> None:
    owned, _org = _owner(client, "files.ver@example.com")
    file_id = _upload(owned, name="v.txt", data=b"version one").json()["data"]["id"]

    second = owned.post(
        f"/api/v1/files/{file_id}/versions",
        files={"file": ("v.txt", b"version two bytes", "text/plain")},
    )
    assert second.status_code == 201, second.text
    assert second.json()["data"]["current_version"] == 2

    versions = owned.get(f"/api/v1/files/{file_id}/versions").json()["data"]
    assert [v["version"] for v in versions] == [1, 2]

    downloaded = owned.get(f"/api/v1/files/{file_id}/content")
    assert downloaded.content == b"version two bytes"


def test_soft_delete(client: TestClient) -> None:
    owned, _org = _owner(client, "files.del@example.com")
    file_id = _upload(owned).json()["data"]["id"]

    removed = owned.delete(f"/api/v1/files/{file_id}")
    assert removed.status_code == 204

    assert owned.get(f"/api/v1/files/{file_id}").status_code == 404
    listed = owned.get("/api/v1/files").json()["data"]
    assert file_id not in {f["id"] for f in listed}

    with sqlite3.connect(TEST_DB_PATH) as connection:
        row = connection.execute(
            "SELECT deleted_at FROM file WHERE id = ?",
            (file_id.replace("-", ""),),
        ).fetchone()
    assert row is not None
    assert row[0] is not None


def test_audit_written(client: TestClient) -> None:
    import asyncio

    from sqlalchemy import text

    from app.core.database import engine

    owned, _org = _owner(client, "files.audit@example.com")
    file_id = _upload(owned, name="a.txt", data=b"audit one").json()["data"]["id"]
    owned.post(
        f"/api/v1/files/{file_id}/versions",
        files={"file": ("a.txt", b"audit two", "text/plain")},
    )

    async def fetch() -> list[str]:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT action_type FROM audit_record WHERE entity_type = 'file'"),
            )
            return [row[0] for row in result.all()]

    actions = asyncio.run(fetch())
    assert "FILE_UPLOADED" in actions
    assert "FILE_VERSION_ADDED" in actions


def test_cyrillic_filename_download(client: TestClient) -> None:
    from urllib.parse import unquote

    owned, _org = _owner(client, "files.cyr@example.com")
    original = "Отчёт за август.txt"
    created = _upload(owned, name=original, data=b"otchet")
    assert created.status_code == 201
    file_id = created.json()["data"]["id"]

    downloaded = owned.get(f"/api/v1/files/{file_id}/content")
    assert downloaded.status_code == 200
    disposition = downloaded.headers["content-disposition"]
    assert disposition.startswith("attachment")
    assert 'filename="' in disposition
    assert "filename*=UTF-8''" in disposition

    ext_part = disposition.split("filename*=UTF-8''", 1)[1].split(";", 1)[0].strip()
    assert unquote(ext_part) == original
