"""End-to-end smoke scenario against a running DevOS backend.

Covers the MVP happy path through the public API contracts:
register -> login -> create organization -> project -> task -> assign ->
comment -> AI action (mock provider) -> search -> notifications.

Every response is validated as an envelope {data, meta, links}; auth is a
Bearer access token. Exit code is non-zero if any step FAILs.

Preparation (clean temp DB + temp storage), from the backend directory:

    $env:DATABASE_URL="sqlite+aiosqlite:///<temp>/e2e.db"
    $env:STORAGE_DIR="<temp>/e2e_storage"
    uv run alembic upgrade head
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8041

Then:

    $env:E2E_BASE_URL="http://127.0.0.1:8041/api/v1"
    uv run python ../scripts/e2e_smoke.py

Base URL override: env E2E_BASE_URL (default http://127.0.0.1:8000/api/v1).
"""

import os
import sys
import uuid
from typing import Any

import httpx

BASE = os.environ.get("E2E_BASE_URL", "http://127.0.0.1:8000/api/v1")
PASSWORD = "e2e-smoke-pass-123"

_results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, evidence: str = "") -> None:
    _results.append((name, bool(ok), evidence))
    print(f"{name:42} -> {'PASS' if ok else 'FAIL'}  {evidence}")


def envelope(response: httpx.Response) -> dict[str, Any]:
    body = response.json()
    if not isinstance(body, dict) or not {"data", "meta", "links"} <= set(body):
        raise AssertionError(f"response is not an envelope: {body}")
    return body


def main() -> int:
    client = httpx.Client(timeout=30)
    run = uuid.uuid4().hex[:8]
    email = f"e2e-{run}@smoke.test"
    try:
        health = client.get(f"{BASE}/health")
        check("health", health.status_code == 200, f"status={health.json().get('status')}")

        reg = client.post(
            f"{BASE}/auth/register",
            json={"email": email, "password": PASSWORD, "displayName": "E2E User"},
        )
        check("register", reg.status_code == 201, f"status={reg.status_code}")
        check("register envelope", set(envelope(reg)) == {"data", "meta", "links"})

        login = client.post(f"{BASE}/auth/login", json={"email": email, "password": PASSWORD})
        tokens = envelope(login)["data"]["tokens"]
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        check(
            "login -> bearer access token",
            login.status_code == 200 and bool(tokens.get("access_token")),
            f"status={login.status_code}",
        )

        org = client.post(
            f"{BASE}/organizations",
            json={"name": f"E2E Org {run}"},
            headers=headers,
        )
        org_id = envelope(org)["data"]["id"]
        check("create organization", org.status_code == 201, f"org={org_id[:8]}")

        project_name = f"E2E Project {run}"
        project = client.post(
            f"{BASE}/projects",
            json={"name": project_name, "description": "e2e smoke"},
            headers=headers,
        )
        project_id = envelope(project)["data"]["id"]
        check("create project", project.status_code == 201, f"project={project_id[:8]}")

        task = client.post(
            f"{BASE}/tasks",
            json={"project_id": project_id, "title": "E2E task", "priority": "high"},
            headers=headers,
        )
        task_id = envelope(task)["data"]["id"]
        check("create task", task.status_code == 201, f"task={task_id[:8]}")

        me = envelope(client.get(f"{BASE}/auth/me", headers=headers))["data"]
        assigned = client.patch(
            f"{BASE}/tasks/{task_id}",
            json={"assignee_id": me["id"]},
            headers=headers,
        )
        check(
            "assign task to self",
            assigned.status_code == 200
            and envelope(assigned)["data"]["assignee_id"] == me["id"],
            f"status={assigned.status_code}",
        )

        comment = client.post(
            f"{BASE}/tasks/{task_id}/comments",
            json={"body": "e2e comment"},
            headers=headers,
        )
        check("create comment", comment.status_code == 201, f"status={comment.status_code}")

        action = client.post(
            f"{BASE}/ai/actions",
            json={
                "action_type": "plan",
                "input_text": "Спланировать демонстрацию MVP прототипа DevOS",
                "project_id": project_id,
                "task_id": task_id,
                "document_ids": [],
            },
            headers=headers,
        )
        detail = envelope(action)["data"]
        check(
            "ai action completed (mock)",
            action.status_code == 200
            and detail["status"] == "completed"
            and detail["result"] is not None,
            f"provider={detail['provider']} status={detail['status']}",
        )

        search = client.get(f"{BASE}/search", params={"q": project_name}, headers=headers)
        search_body = envelope(search)
        found = any(p["id"] == project_id for p in search_body["data"]["projects"])
        check(
            "search finds project",
            search.status_code == 200 and found,
            f"counts={search_body['meta']['counts']}",
        )

        notifs = client.get(f"{BASE}/notifications", headers=headers)
        notif_body = envelope(notifs)
        titles = [n["title"] for n in notif_body["data"]]
        check(
            "notifications: TaskAssigned delivered",
            notifs.status_code == 200 and any("назначена" in t for t in titles),
            f"total={notif_body['meta']['pagination']['totalItems']}",
        )
    except Exception as exc:  # noqa: BLE001
        check("scenario executed", False, f"exception={exc!r}")
    finally:
        client.close()

    failed = [name for name, ok, _ in _results if not ok]
    print("-" * 72)
    print(f"TOTAL: {len(_results)}  PASS: {len(_results) - len(failed)}  FAIL: {len(failed)}")
    for name in failed:
        print(f"  FAIL: {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
