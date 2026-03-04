import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_delete_department_cascade(client: AsyncClient):
    # root
    resp = await client.post("/departments/", json={"name": "root", "parent_id": None})
    root_id = resp.json()["id"]

    # child
    resp = await client.post(
        "/departments/", json={"name": "child", "parent_id": root_id}
    )
    child_id = resp.json()["id"]

    # grandchild
    resp = await client.post(
        "/departments/", json={"name": "grand", "parent_id": child_id}
    )
    grand_id = resp.json()["id"]

    # employee
    await client.post(
        f"/departments/{child_id}/employees/",
        json={
            "full_name": "Ivan Petrov",
            "position": "Dev",
            "hired_at": "2024-01-01",
        },
    )

    # delete child cascade
    resp = await client.delete(f"/departments/{child_id}?mode=cascade")
    assert resp.status_code == 204

    # child должен исчезнуть
    resp = await client.get(f"/departments/{child_id}")
    assert resp.status_code == 404

    # grandchild тоже
    resp = await client.get(f"/departments/{grand_id}")
    assert resp.status_code == 404
