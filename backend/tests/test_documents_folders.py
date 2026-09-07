import sqlite3
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers

TEST_DB_PATH = Path(__file__).parent / "_test.db"


def _owner(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"DocOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _upload_file(
    owned: AuthorizedClient,
    name: str = "doc.txt",
    data: bytes = b"plain text body",
    mime: str = "text/plain",
) -> str:
    response = owned.post("/api/v1/files", files={"file": (name, data, mime)})
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"]


def test_nested_folders_and_soft_delete(client: TestClient) -> None:
    owned, _org = _owner(client, "folders.nest@example.com")

    parent = owned.post("/api/v1/documents/folders", json={"name": "Parent"})
    assert parent.status_code == 201
    parent_id = parent.json()["data"]["id"]

    child = owned.post(
        "/api/v1/documents/folders",
        json={"name": "Child", "parent_id": parent_id},
    )
    assert child.status_code == 201
    child_id = child.json()["data"]["id"]
    assert child.json()["data"]["parent_id"] == parent_id

    listed_children = owned.get(f"/api/v1/documents/folders?parent_id={parent_id}").json()["data"]
    assert {f["id"] for f in listed_children} == {child_id}

    deleted = owned.delete(f"/api/v1/documents/folders/{child_id}")
    assert deleted.status_code == 204
    after = owned.get(f"/api/v1/documents/folders?parent_id={parent_id}").json()["data"]
    assert child_id not in {f["id"] for f in after}

    with sqlite3.connect(TEST_DB_PATH) as connection:
        row = connection.execute(
            "SELECT deleted_at FROM folder WHERE id = ?",
            (child_id.replace("-", ""),),
        ).fetchone()
    assert row is not None and row[0] is not None


def test_folder_not_empty_blocks_delete(client: TestClient) -> None:
    owned, _org = _owner(client, "folders.empty@example.com")
    parent = owned.post("/api/v1/documents/folders", json={"name": "P"}).json()["data"]
    owned.post(
        "/api/v1/documents/folders",
        json={"name": "C", "parent_id": parent["id"]},
    )
    response = owned.delete(f"/api/v1/documents/folders/{parent['id']}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FOLDER_NOT_EMPTY"


def test_folder_with_document_blocks_delete(client: TestClient) -> None:
    owned, _org = _owner(client, "folders.doc@example.com")
    folder = owned.post("/api/v1/documents/folders", json={"name": "Docs"}).json()["data"]
    owned.post(
        "/api/v1/documents",
        json={
            "title": "in folder",
            "relative_path": "99_AI/03_GLOSSARY.md",
            "folder_id": folder["id"],
        },
    )
    response = owned.delete(f"/api/v1/documents/folders/{folder['id']}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FOLDER_NOT_EMPTY"


def test_document_from_uploaded_text_file(client: TestClient) -> None:
    owned, _org = _owner(client, "docs.filetext@example.com")
    folder = owned.post("/api/v1/documents/folders", json={"name": "Uploads"}).json()["data"]
    file_id = _upload_file(owned, name="note.txt", data=b"hello from file", mime="text/plain")

    created = owned.post(
        "/api/v1/documents",
        json={"title": "Note", "file_id": file_id, "folder_id": folder["id"]},
    )
    assert created.status_code == 201, created.text
    doc = created.json()["data"]
    assert doc["file_id"] == file_id
    assert doc["folder_id"] == folder["id"]
    assert doc["relative_path"] is None

    content = owned.get(f"/api/v1/documents/{doc['id']}").json()["data"]
    assert content["content"] == "hello from file"
    assert content["is_binary"] is False
    assert content["download_url"] is None
    assert content["missing"] is False


def test_document_from_binary_file(client: TestClient) -> None:
    owned, _org = _owner(client, "docs.filebin@example.com")
    file_id = _upload_file(
        owned, name="blob.bin", data=bytes([0, 1, 2, 250, 251]), mime="application/octet-stream"
    )
    doc = owned.post(
        "/api/v1/documents",
        json={"title": "Binary", "file_id": file_id},
    ).json()["data"]

    content = owned.get(f"/api/v1/documents/{doc['id']}").json()["data"]
    assert content["is_binary"] is True
    assert content["content"] is None
    assert content["download_url"] == f"/api/v1/files/{file_id}/content"


def test_invalid_document_source(client: TestClient) -> None:
    owned, _org = _owner(client, "docs.source@example.com")
    both = owned.post(
        "/api/v1/documents",
        json={
            "title": "both",
            "relative_path": "99_AI/03_GLOSSARY.md",
            "file_id": str(uuid.uuid4()),
        },
    )
    assert both.status_code == 422
    assert both.json()["error"]["code"] == "INVALID_DOCUMENT_SOURCE"

    neither = owned.post("/api/v1/documents", json={"title": "neither"})
    assert neither.status_code == 422
    assert neither.json()["error"]["code"] == "INVALID_DOCUMENT_SOURCE"


def test_cross_org_file_and_folder_not_found(client: TestClient) -> None:
    owned, _org = _owner(client, "docs.xo.a@example.com")
    file_id = _upload_file(owned, name="a.txt", data=b"a secret", mime="text/plain")
    folder_id = owned.post(
        "/api/v1/documents/folders", json={"name": "A folder"}
    ).json()["data"]["id"]

    outsider, _ = _owner(client, "docs.xo.b@example.com")
    bad_file = outsider.post(
        "/api/v1/documents", json={"title": "steal", "file_id": file_id}
    )
    assert bad_file.status_code == 404
    assert bad_file.json()["error"]["code"] == "FILE_NOT_FOUND"

    bad_folder = outsider.post(
        "/api/v1/documents",
        json={"title": "steal", "relative_path": "99_AI/03_GLOSSARY.md", "folder_id": folder_id},
    )
    assert bad_folder.status_code == 404
    assert bad_folder.json()["error"]["code"] == "FOLDER_NOT_FOUND"

    bad_folder_get = outsider.delete(f"/api/v1/documents/folders/{folder_id}")
    assert bad_folder_get.status_code == 404


def test_folder_parent_foreign_org_not_found(client: TestClient) -> None:
    owned, _org = _owner(client, "docs.fp.a@example.com")
    folder_id = owned.post(
        "/api/v1/documents/folders", json={"name": "A root"}
    ).json()["data"]["id"]
    outsider, _ = _owner(client, "docs.fp.b@example.com")
    response = outsider.post(
        "/api/v1/documents/folders", json={"name": "nested", "parent_id": folder_id}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FOLDER_NOT_FOUND"


def test_documents_list_filter_by_folder(client: TestClient) -> None:
    owned, _org = _owner(client, "docs.filter@example.com")
    folder = owned.post("/api/v1/documents/folders", json={"name": "F"}).json()["data"]
    owned.post(
        "/api/v1/documents",
        json={
            "title": "inside",
            "relative_path": "99_AI/03_GLOSSARY.md",
            "folder_id": folder["id"],
        },
    )
    owned.post(
        "/api/v1/documents",
        json={"title": "outside", "relative_path": "99_AI/01_PROJECT_CONTEXT.md"},
    )
    inside = owned.get(f"/api/v1/documents?folder_id={folder['id']}").json()["data"]
    assert {d["title"] for d in inside} == {"inside"}
