from typing import Any

from fastapi.testclient import TestClient

from app.modules.crm import events as crm_events
from tests.auth_helper import AuthorizedClient, auth_headers


def _owner(client: TestClient, email: str) -> tuple[AuthorizedClient, str]:
    headers = auth_headers(client, email, create_org=True, org_name=f"CrmOrg-{email}")
    owned = AuthorizedClient(client, headers)
    org_id = owned.get("/api/v1/organizations").json()["data"][0]["id"]
    return owned, org_id


def _invite_employee(
    client: TestClient, owned: AuthorizedClient, org_id: str, email: str
) -> AuthorizedClient:
    invited = owned.post(
        f"/api/v1/organizations/{org_id}/users",
        json={"email": email, "displayName": "Emp"},
    ).json()["data"]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": invited["generated_password"]},
    ).json()["data"]["tokens"]["access_token"]
    return AuthorizedClient(client, {"Authorization": f"Bearer {login}"})


def test_customer_crud_and_archive_restore(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.crud@example.com")
    created = owned.post("/api/v1/customers", json={"name": "Acme", "description": "vip"})
    assert created.status_code == 201, created.text
    cid = created.json()["data"]["id"]
    assert created.json()["data"]["status"] == "lead"

    listed = owned.get("/api/v1/customers").json()
    assert cid in {c["id"] for c in listed["data"]}

    patched = owned.patch(f"/api/v1/customers/{cid}", json={"description": "top-tier"})
    assert patched.status_code == 200
    assert patched.json()["data"]["description"] == "top-tier"

    archived = owned.post(f"/api/v1/customers/{cid}/archive")
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "archived"

    restored = owned.post(f"/api/v1/customers/{cid}/restore")
    assert restored.status_code == 200
    assert restored.json()["data"]["status"] == "active"

    filtered = owned.get("/api/v1/customers", params={"status": "active"}).json()["data"]
    assert cid in {c["id"] for c in filtered}


def test_customer_invalid_status(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.status@example.com")
    response = owned.post("/api/v1/customers", json={"name": "X", "status": "bogus"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_STATUS"


def test_contacts_notes_tags(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.sub@example.com")
    cid = owned.post("/api/v1/customers", json={"name": "SubCo"}).json()["data"]["id"]

    contact = owned.post(
        f"/api/v1/customers/{cid}/contacts",
        json={"name": "John", "email": "john@corp.test", "phone": "+1"},
    )
    assert contact.status_code == 201
    bad_email = owned.post(
        f"/api/v1/customers/{cid}/contacts",
        json={"name": "Bad", "email": "not-an-email"},
    )
    assert bad_email.status_code == 422
    assert bad_email.json()["error"]["code"] == "INVALID_CONTACT_EMAIL"

    note = owned.post(f"/api/v1/customers/{cid}/notes", json={"body": "call tomorrow"})
    assert note.status_code == 201
    assert note.json()["data"]["author_name"] == "crm.sub"

    tag = owned.post("/api/v1/tags", json={"name": "important"})
    assert tag.status_code == 201
    tag_id = tag.json()["data"]["id"]
    dup = owned.post("/api/v1/tags", json={"name": "important"})
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "TAG_NAME_EXISTS"

    attached = owned.post(f"/api/v1/customers/{cid}/tags", json={"tagId": tag_id})
    assert attached.status_code == 200
    assert tag_id in {t["id"] for t in attached.json()["data"]["tags"]}

    detached = owned.delete(f"/api/v1/customers/{cid}/tags/{tag_id}")
    assert detached.status_code == 200
    assert tag_id not in {t["id"] for t in detached.json()["data"]["tags"]}


def test_customer_soft_delete(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.del@example.com")
    cid = owned.post("/api/v1/customers", json={"name": "Doomed"}).json()["data"]["id"]
    assert owned.delete(f"/api/v1/customers/{cid}").status_code == 204
    assert owned.get(f"/api/v1/customers/{cid}").status_code == 404
    assert cid not in {c["id"] for c in owned.get("/api/v1/customers").json()["data"]}


def test_employee_cannot_create_customer(client: TestClient) -> None:
    owned, org_id = _owner(client, "crm.emp@example.com")
    employee = _invite_employee(client, owned, org_id, "crm.emp.user@example.com")
    response = employee.post("/api/v1/customers", json={"name": "Nope"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_cross_org_isolation(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.xo.a@example.com")
    cid = owned.post("/api/v1/customers", json={"name": "SecretCo"}).json()["data"]["id"]
    tag_id = owned.post("/api/v1/tags", json={"name": "vip"}).json()["data"]["id"]

    outsider, _ = _owner(client, "crm.xo.b@example.com")
    assert outsider.get(f"/api/v1/customers/{cid}").status_code == 404
    assert outsider.patch(f"/api/v1/customers/{cid}", json={"name": "x"}).status_code == 404
    assert outsider.post(f"/api/v1/customers/{cid}/notes", json={"body": "x"}).status_code == 404
    assert outsider.post(f"/api/v1/customers/{cid}/tags", json={"tagId": tag_id}).status_code == 404


def test_project_link_foreign_customer_404(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.link.a@example.com")
    cid = owned.post("/api/v1/customers", json={"name": "LinkedCo"}).json()["data"]["id"]
    outsider, _ = _owner(client, "crm.link.b@example.com")
    project = outsider.post("/api/v1/projects", json={"name": "P"}).json()["data"]
    response = outsider.patch(
        f"/api/v1/projects/{project['id']}", json={"customer_id": cid}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


def test_project_link_own_customer(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.link.ok@example.com")
    cid = owned.post("/api/v1/customers", json={"name": "MyCo"}).json()["data"]["id"]
    project = owned.post("/api/v1/projects", json={"name": "P"}).json()["data"]
    linked = owned.patch(f"/api/v1/projects/{project['id']}", json={"customer_id": cid})
    assert linked.status_code == 200
    assert linked.json()["data"]["customer_id"] == cid
    unlinked = owned.patch(f"/api/v1/projects/{project['id']}", json={"customer_id": None})
    assert unlinked.status_code == 200
    assert unlinked.json()["data"]["customer_id"] is None


def test_projects_filter_by_customer(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.filter@example.com")
    cid = owned.post("/api/v1/customers", json={"name": "FilterCo"}).json()["data"]["id"]
    other = owned.post("/api/v1/customers", json={"name": "OtherCo"}).json()["data"]["id"]
    linked = owned.post("/api/v1/projects", json={"name": "Linked"}).json()["data"]["id"]
    owned.patch(f"/api/v1/projects/{linked}", json={"customer_id": cid})
    owned.post("/api/v1/projects", json={"name": "Unlinked"})

    filtered = owned.get("/api/v1/projects", params={"customer_id": cid}).json()["data"]
    assert {p["id"] for p in filtered} == {linked}
    empty = owned.get("/api/v1/projects", params={"customer_id": other}).json()["data"]
    assert empty == []


def test_search_finds_customer_cyrillic(client: TestClient) -> None:
    owned, _org = _owner(client, "crm.search@example.com")
    owned.post("/api/v1/customers", json={"name": "Отчётный клиент"})
    body = owned.get("/api/v1/search", params={"q": "ОТЧЁТНЫЙ"}).json()
    assert body["meta"]["counts"]["customers"] >= 1
    assert any(c["name"] == "Отчётный клиент" for c in body["data"]["customers"])


def test_crm_events_published(client: TestClient, monkeypatch) -> None:
    captured: list[dict[str, Any]] = []

    async def capture(event: dict[str, Any]) -> None:
        captured.append(event)

    monkeypatch.setattr(crm_events, "publish_event", capture)
    owned, _org = _owner(client, "crm.events@example.com")
    cid = owned.post("/api/v1/customers", json={"name": "EventCo"}).json()["data"]["id"]
    owned.post(f"/api/v1/customers/{cid}/archive")

    types = [e["eventType"] for e in captured]
    assert "CustomerCreated" in types
    assert "CustomerArchived" in types
    created = next(e for e in captured if e["eventType"] == "CustomerCreated")
    assert created["payload"]["customerId"] == cid
    assert created["payload"]["name"] == "EventCo"
    assert created["metadata"]["sourceModule"] == "CRM"
