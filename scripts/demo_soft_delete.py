"""Manual demonstration of soft delete + PROJECT_NOT_EMPTY guard.

Run with backend serving on 127.0.0.1:8010:
    cd backend && uv run python ../scripts/demo_soft_delete.py
"""

import sqlite3
import sys
from pathlib import Path

import httpx

BASE = "http://127.0.0.1:8010/api/v1"
DB_PATH = Path(__file__).resolve().parents[1] / "devos.db"


def main() -> int:
    client = httpx.Client(base_url=BASE, timeout=30)

    project_id = client.post(
        "/projects",
        json={"name": "Demo Guard Project"},
    ).json()["data"]["id"]
    print(f"1. created project            {project_id}")

    task_id = client.post(
        "/tasks",
        json={"project_id": project_id, "title": "demo task"},
    ).json()["data"]["id"]
    print(f"2. created task in project    {task_id}")

    conflict = client.delete(f"/projects/{project_id}")
    error = conflict.json()["error"]
    print(
        f"3. DELETE project             -> {conflict.status_code} "
        f"{error['code']} details={error['details']}"
    )
    assert conflict.status_code == 409
    assert error["code"] == "PROJECT_NOT_EMPTY"

    removed = client.delete(f"/tasks/{task_id}")
    print(f"4. DELETE task                -> {removed.status_code}")
    assert removed.status_code == 204

    second = client.delete(f"/projects/{project_id}")
    print(f"5. DELETE project again       -> {second.status_code}")
    assert second.status_code == 204

    fetched = client.get(f"/projects/{project_id}")
    print(f"6. GET deleted project        -> {fetched.status_code} "
          f"{fetched.json()['error']['code']}")
    assert fetched.status_code == 404

    hex_id = project_id.replace("-", "")
    connection = sqlite3.connect(DB_PATH)
    row = connection.execute(
        "SELECT name, status, deleted_at FROM project WHERE id = ?",
        (hex_id,),
    ).fetchone()
    connection.close()
    print(f"7. DB row still present       -> name={row[0]!r} status={row[1]!r} "
          f"deleted_at={row[2]}")
    assert row is not None and row[2] is not None

    print("DEMONSTRATION PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
