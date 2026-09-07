from fastapi.testclient import TestClient

from tests.auth_helper import AuthorizedClient, auth_headers


def _auth(client: TestClient, email: str = "ai.user@example.com") -> AuthorizedClient:
    headers = auth_headers(
        client,
        email,
        create_org=True,
        org_name=f"AiOrg-{email}",
    )
    return AuthorizedClient(client, headers)


def _prepare_context(client: TestClient) -> tuple[dict[str, str], str, str]:
    user = _auth(client)
    project = user.post(
        "/api/v1/projects",
        json={"name": "AI Flow Project", "description": "project for ai smoke"},
    ).json()["data"]
    document = user.post(
        "/api/v1/documents",
        json={
            "title": "MVP Spec",
            "relative_path": "02_PRODUCT/13_MVP_Specification.md",
            "category": "product",
        },
    ).json()["data"]
    return dict(user._headers), project["id"], document["id"]


def _run_action(
    client: TestClient,
    headers: dict[str, str],
    project_id: str,
    document_id: str,
) -> dict:
    response = client.post(
        "/api/v1/ai/actions",
        json={
            "action_type": "analyze",
            "input_text": "Проанализировать готовность MVP прототипа DevOS",
            "project_id": project_id,
            "document_ids": [document_id],
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_ai_analyze_action_persists_result(client: TestClient) -> None:
    headers, project_id, document_id = _prepare_context(client)
    user = AuthorizedClient(client, headers)
    body = _run_action(client, headers, project_id, document_id)

    assert set(body.keys()) == {"data", "meta", "links"}
    action = body["data"]
    assert action["status"] == "completed"
    assert action["provider"] == "mock"
    assert action["result"] is not None
    assert len(action["result"]["content"]) > 0

    history = user.get(
        f"/api/v1/ai/actions?project_id={project_id}",
    )
    assert history.status_code == 200
    assert history.json()["meta"]["pagination"]["totalItems"] >= 1

    fetched = user.get(f"/api/v1/ai/actions/{action['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["result"]["id"] == action["result"]["id"]


def test_ai_action_types_supported(client: TestClient) -> None:
    user = _auth(client)
    for action_type in ("plan", "execute", "summarize"):
        response = user.post(
            "/api/v1/ai/actions",
            json={"action_type": action_type, "input_text": "Подготовить релиз прототипа"},
        )
        assert response.status_code == 200, action_type
        assert response.json()["data"]["status"] == "completed"


def test_ai_invalid_action_type_rejected(client: TestClient) -> None:
    user = _auth(client)
    response = user.post(
        "/api/v1/ai/actions",
        json={"action_type": "destroy", "input_text": "bad"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ACTION_TYPE"


def test_dashboard_aggregates(client: TestClient) -> None:
    user = _auth(client)
    response = user.get("/api/v1/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "meta", "links"}
    stats = body["data"]["stats"]
    assert set(stats.keys()) == {"projects", "tasks", "documents", "ai_actions"}


def test_ai_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/actions",
        json={"action_type": "analyze", "input_text": "x"},
    )
    assert response.status_code == 401
    assert client.get("/api/v1/ai/actions").status_code == 401
