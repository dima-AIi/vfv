import uuid

from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers

ENVELOPE_KEYS = {"data", "meta", "links"}


def _owned(client: TestClient, email: str = "contract@example.com") -> AuthorizedClient:
    return AuthorizedClient(
        client,
        auth_headers(client, email, create_org=True, org_name=f"Contract Org {email}"),
    )


def _create_projects(owned: AuthorizedClient, count: int) -> list[str]:
    ids: list[str] = []
    for i in range(count):
        body = owned.post(
            "/api/v1/projects",
            json={"name": f"Contract Project {i:02d}"},
        ).json()
        ids.append(body["data"]["id"])
    return ids


def test_envelope_shape_single_resource_endpoints(client: TestClient) -> None:
    owned = _owned(client)
    project = owned.post(
        "/api/v1/projects",
        json={"name": "Envelope Single"},
    )
    assert project.status_code == 201
    assert set(project.json().keys()) == ENVELOPE_KEYS

    project_id = project.json()["data"]["id"]

    task = owned.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "t"},
    )
    assert set(task.json().keys()) == ENVELOPE_KEYS
    task_id = task.json()["data"]["id"]

    document = owned.post(
        "/api/v1/documents",
        json={
            "title": "Doc",
            "relative_path": "99_AI/03_GLOSSARY.md",
        },
    )
    assert set(document.json().keys()) == ENVELOPE_KEYS
    document_id = document.json()["data"]["id"]

    for path in (
        f"/api/v1/projects/{project_id}",
        f"/api/v1/tasks/{task_id}",
        f"/api/v1/documents/{document_id}",
    ):
        assert set(owned.get(path).json().keys()) == ENVELOPE_KEYS, path

    providers = owned.get("/api/v1/ai/providers")
    assert providers.status_code == 200
    assert set(providers.json().keys()) == ENVELOPE_KEYS
    assert providers.json()["data"]["active"] == "mock"

    action = owned.post(
        "/api/v1/ai/actions",
        json={"action_type": "summarize", "input_text": "проверка конверта"},
    )
    assert set(action.json().keys()) == ENVELOPE_KEYS
    action_id = action.json()["data"]["id"]
    fetched_action = owned.get(f"/api/v1/ai/actions/{action_id}")
    assert set(fetched_action.json().keys()) == ENVELOPE_KEYS


def test_envelope_shape_collection_and_dashboard(client: TestClient) -> None:
    owned = _owned(client)
    _create_projects(owned, 2)

    for path in (
        "/api/v1/projects",
        "/api/v1/documents",
        "/api/v1/documents/catalog",
        "/api/v1/ai/actions",
    ):
        response = owned.get(path)
        assert response.status_code == 200, path
        body = response.json()
        assert set(body.keys()) == ENVELOPE_KEYS, path
        assert isinstance(body["data"], list), path
        assert isinstance(body["meta"], dict), path

    dashboard = owned.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert set(body.keys()) == ENVELOPE_KEYS
    assert set(body["meta"].keys()) == set()


def test_health_not_enveloped(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert ENVELOPE_KEYS.intersection(body.keys()) == set()


def test_pagination_defaults(client: TestClient) -> None:
    owned = _owned(client)
    _create_projects(owned, 3)

    body = owned.get("/api/v1/projects").json()
    pagination = body["meta"]["pagination"]
    assert pagination["page"] == 1
    assert pagination["pageSize"] == 25
    assert pagination["totalItems"] >= 3
    assert pagination["totalPages"] >= 1
    assert pagination["hasNext"] is False
    assert pagination["hasPrevious"] is False


def test_pagination_page_math(client: TestClient) -> None:
    owned = _owned(client)
    _create_projects(owned, 3)

    page1 = owned.get("/api/v1/projects?page=1&pageSize=2").json()
    p1 = page1["meta"]["pagination"]
    assert len(page1["data"]) == 2
    assert p1["totalItems"] >= 3
    assert p1["totalPages"] == (p1["totalItems"] + 1) // 2
    assert p1["hasNext"] is True
    assert p1["hasPrevious"] is False

    last_page = p1["totalPages"]
    page_last = owned.get(f"/api/v1/projects?page={last_page}&pageSize=2").json()
    pl = page_last["meta"]["pagination"]
    assert pl["hasNext"] is False
    assert pl["hasPrevious"] is True
    assert len(page_last["data"]) >= 1


def test_pagination_clamps_page_size(client: TestClient) -> None:
    owned = _owned(client)
    too_large = owned.get("/api/v1/projects?pageSize=1000").json()
    assert too_large["meta"]["pagination"]["pageSize"] == 100

    too_small = owned.get("/api/v1/projects?pageSize=0").json()
    assert too_small["meta"]["pagination"]["pageSize"] == 1


def test_sort_created_at_ordering(client: TestClient) -> None:
    owned = _owned(client)
    ids = _create_projects(owned, 3)

    desc_ids = [
        p["id"]
        for p in owned.get("/api/v1/projects?sort=-createdAt&pageSize=100").json()["data"]
        if p["id"] in ids
    ]
    assert desc_ids == list(reversed(ids))

    asc_ids = [
        p["id"]
        for p in owned.get("/api/v1/projects?sort=createdAt&pageSize=100").json()["data"]
        if p["id"] in ids
    ]
    assert asc_ids == ids


def test_invalid_sort_rejected_on_all_list_endpoints(client: TestClient) -> None:
    owned = _owned(client)
    project_id = _create_projects(owned, 1)[0]
    paths = (
        "/api/v1/projects?sort=foo",
        f"/api/v1/tasks?project_id={project_id}&sort=foo",
        "/api/v1/documents?sort=foo",
        "/api/v1/documents/catalog?sort=foo",
        "/api/v1/ai/actions?sort=foo",
    )
    for path in paths:
        response = owned.get(path)
        assert response.status_code == 422, path
        assert response.json()["error"]["code"] == "INVALID_SORT", path


def test_request_id_echoed_from_incoming_header(client: TestClient) -> None:
    owned = _owned(client)
    incoming = "test-request-id-123"
    response = owned.get(
        "/api/v1/projects?page=1&pageSize=5",
        headers={"X-Request-ID": incoming},
    )
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == incoming
    assert response.headers["X-Correlation-ID"] == incoming


def test_request_id_inside_error_payload(client: TestClient) -> None:
    owned = _owned(client)
    incoming = "error-trace-abc"
    response = owned.get(
        f"/api/v1/projects/{uuid.uuid4()}",
        headers={"X-Correlation-ID": incoming},
    )
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["requestId"] == incoming
    assert response.headers["X-Request-ID"] == incoming


def test_request_id_generated_when_missing(client: TestClient) -> None:
    owned = _owned(client)
    response = owned.get("/api/v1/projects")
    header_value = response.headers["X-Request-ID"]
    assert header_value == response.headers["X-Correlation-ID"]
    uuid.UUID(header_value)


def test_dangerous_request_id_is_regenerated(client: TestClient) -> None:
    owned = _owned(client)
    response = owned.get(
        "/api/v1/projects",
        headers={"X-Request-ID": "bad-id\nwith-newline"},
    )
    header_value = response.headers["X-Request-ID"]
    assert "\n" not in header_value
    uuid.UUID(header_value)
