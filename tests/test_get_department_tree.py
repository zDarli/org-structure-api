import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_department_tree(client: AsyncClient):
    # root
    resp = await client.post("/departments/", json={"name": "root", "parent_id": None})
    root_id = resp.json()["id"]

    # child
    resp = await client.post(
        "/departments/", json={"name": "child", "parent_id": root_id}
    )
    child_id = resp.json()["id"]

    # employee
    await client.post(
        f"/departments/{child_id}/employees/",
        json={
            "full_name": "Ivan Petrov",
            "position": "Dev",
            "hired_at": "2024-01-01",
        },
    )

    # get tree
    resp = await client.get(f"/departments/{root_id}?depth=2&include_employees=true")

    assert resp.status_code == 200

    data = resp.json()

    # root
    assert data["department"]["id"] == root_id

    # child существует
    assert len(data["children"]) == 1
    assert data["children"][0]["department"]["id"] == child_id

    # employee внутри child
    assert len(data["children"][0]["employees"]) == 1
    assert data["children"][0]["employees"][0]["full_name"] == "Ivan Petrov"
