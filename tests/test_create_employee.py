import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_employee(client: AsyncClient) -> None:
    # сначала департамент
    dep = await client.post("/departments/", json={"name": "IT", "parent_id": None})
    assert dep.status_code == 201, dep.text
    dep_id = dep.json()["id"]
    # создаём сотрудника
    resp = await client.post(
        f"/departments/{dep_id}/employees/",
        json={
            "full_name": "Ivan Petrov",
            "position": "Backend Dev",
            "hired_at": "2024-01-10",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert isinstance(data["id"], int)
    assert data["department_id"] == dep_id
    assert data["full_name"] == "Ivan Petrov"
    assert data["position"] == "Backend Dev"

    # 404 если департамент не существует
    resp2 = await client.post(
        "/departments/999999/employees/",
        json={"full_name": "Ghost", "position": "Nobody", "hired_at": "2024-01-10"},
    )
    assert resp2.status_code == 404, resp2.text
