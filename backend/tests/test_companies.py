from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


def _owner(client: TestClient, email: str) -> AuthorizedClient:
    headers = auth_headers(client, email, create_org=True, org_name=f"CoOrg-{email}")
    return AuthorizedClient(client, headers)


def test_company_crud(client: TestClient) -> None:
    owned = _owner(client, "co.crud@example.com")
    created = owned.post("/api/v1/companies", json={"name": "Acme Corp"})
    assert created.status_code == 201, created.text
    co_id = created.json()["data"]["id"]

    listed = owned.get("/api/v1/companies").json()["data"]
    assert co_id in {c["id"] for c in listed}

    fetched = owned.get(f"/api/v1/companies/{co_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["name"] == "Acme Corp"

    patched = owned.patch(f"/api/v1/companies/{co_id}", json={"name": "Acme LLC"})
    assert patched.status_code == 200
    assert patched.json()["data"]["name"] == "Acme LLC"

    assert owned.delete(f"/api/v1/companies/{co_id}").status_code == 204
    assert owned.get(f"/api/v1/companies/{co_id}").status_code == 404


def test_company_search_filter(client: TestClient) -> None:
    owned = _owner(client, "co.search@example.com")
    owned.post("/api/v1/companies", json={"name": "Gamma Industries"})
    owned.post("/api/v1/companies", json={"name": "Delta Ltd"})
    found = owned.get("/api/v1/companies", params={"q": "gamma"}).json()["data"]
    assert [c["name"] for c in found] == ["Gamma Industries"]


def test_customer_company_link_and_name(client: TestClient) -> None:
    owned = _owner(client, "co.link@example.com")
    co_id = owned.post("/api/v1/companies", json={"name": "LinkCo"}).json()["data"]["id"]
    customer = owned.post(
        "/api/v1/customers", json={"name": "Cust", "company_id": co_id}
    )
    assert customer.status_code == 201
    assert customer.json()["data"]["company_name"] == "LinkCo"
    assert customer.json()["data"]["company"]["id"] == co_id


def test_customer_foreign_company_404(client: TestClient) -> None:
    owned = _owner(client, "co.xo.a@example.com")
    co_id = owned.post("/api/v1/companies", json={"name": "ForeignCo"}).json()["data"]["id"]
    outsider = _owner(client, "co.xo.b@example.com")
    response = outsider.post(
        "/api/v1/customers", json={"name": "Steal", "company_id": co_id}
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "COMPANY_NOT_FOUND"
