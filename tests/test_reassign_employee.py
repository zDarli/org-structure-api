import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_delete_department_reassign_moves_employees(client: AsyncClient):
    # root
    resp = await client.post("/departments/", json={"name": "root", "parent_id": None})
    root_id = resp.json()["id"]

    # child
    resp = await client.post(
        "/departments/", json={"name": "child", "parent_id": root_id}
    )
    child_id = resp.json()["id"]

    # employee в child
    resp = await client.post(
        f"/departments/{child_id}/employees/",
        json={
            "full_name": "Ivan Petrov",
            "position": "Dev",
            "hired_at": "2024-01-01",
        },
    )
    assert resp.status_code == 201
    employee = resp.json()
    employee_id = employee["id"]

    # delete child → reassign to root
    resp = await client.delete(
        f"/departments/{child_id}?mode=reassign&reassign_to_department_id={root_id}"
    )
    assert resp.status_code == 204

    # получаем root с сотрудниками
    resp = await client.get(f"/departments/{root_id}?depth=1&include_employees=true")
    assert resp.status_code == 200

    data = resp.json()

    employee_ids = [e["id"] for e in data["employees"]]

    # сотрудник должен оказаться в root
    assert employee_id in employee_ids
