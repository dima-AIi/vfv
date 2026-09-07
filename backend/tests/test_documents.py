import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers

TEST_DB_PATH = Path(__file__).parent / "_test.db"


def _auth(client: TestClient, email: str = "docs@example.com") -> AuthorizedClient:
    headers = auth_headers(
        client,
        email,
        create_org=True,
        org_name=f"DocsOrg-{email}",
    )
    return AuthorizedClient(client, headers)


def test_document_catalog_lists_repo_docs(client: TestClient) -> None:
    documents = _auth(client)
    response = documents.get("/api/v1/documents/catalog")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "meta", "links"}
    items = body["data"]
    assert len(items) > 0
    assert any(item["relative_path"].startswith("01_ARCHITECTURE/") for item in items)


def test_document_create_and_read_content(client: TestClient) -> None:
    documents = _auth(client)
    created = documents.post(
        "/api/v1/documents",
        json={
            "title": "Architecture Rules",
            "relative_path": "01_ARCHITECTURE/05A_Architecture_Rules.md",
            "category": "architecture",
        },
    )
    assert created.status_code == 201
    with sqlite3.connect(TEST_DB_PATH) as connection:
        org_id = connection.execute(
            "SELECT organization_id FROM document WHERE id = ?",
            (created.json()["data"]["id"].replace("-", ""),),
        ).fetchone()[0]
    assert org_id is not None

    content = documents.get(f"/api/v1/documents/{created.json()['data']['id']}")
    assert content.status_code == 200
    data = content.json()["data"]
    assert data["missing"] is False
    assert "DevOS" in (data["content"] or "")


def test_document_path_traversal_blocked(client: TestClient) -> None:
    documents = _auth(client)
    for evil_path in (
        "../../../.git/config",
        "99_AI/../../../.gitignore",
        "backend/pyproject.toml",
    ):
        response = documents.post(
            "/api/v1/documents",
            json={"title": "evil", "relative_path": evil_path},
        )
        assert response.status_code == 422, evil_path
        assert response.json()["error"]["code"] == "INVALID_DOCUMENT_PATH"


def test_document_outside_allowed_roots_rejected(client: TestClient) -> None:
    documents = _auth(client)
    response = documents.post(
        "/api/v1/documents",
        json={"title": "root file", "relative_path": "README_ROOT.md"},
    )
    assert response.status_code == 422


def test_document_soft_delete(client: TestClient) -> None:
    documents = _auth(client, "docs.soft@example.com")
    created = documents.post(
        "/api/v1/documents",
        json={"title": "doomed", "relative_path": "99_AI/03_GLOSSARY.md"},
    )
    assert created.status_code == 201
    doc_id = created.json()["data"]["id"]

    removed = documents.delete(f"/api/v1/documents/{doc_id}")
    assert removed.status_code == 204

    assert documents.get(f"/api/v1/documents/{doc_id}").status_code == 404
    listed = documents.get("/api/v1/documents").json()["data"]
    assert doc_id not in {d["id"] for d in listed}

    with sqlite3.connect(TEST_DB_PATH) as connection:
        row = connection.execute(
            "SELECT deleted_at FROM document WHERE id = ?",
            (doc_id.replace("-", ""),),
        ).fetchone()
    assert row is not None
    assert row[0] is not None


def test_file_document_relative_path_is_null(client: TestClient) -> None:
    documents = _auth(client, "docs.nullpath@example.com")
    upload = documents.post(
        "/api/v1/files",
        files={"file": ("note.txt", b"body", "text/plain")},
    )
    assert upload.status_code == 201
    file_id = upload.json()["data"]["id"]
    created = documents.post(
        "/api/v1/documents",
        json={"title": "Note", "file_id": file_id},
    )
    assert created.status_code == 201
    assert created.json()["data"]["relative_path"] is None
