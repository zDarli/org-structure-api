import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_delete_department_reassign(client: AsyncClient):
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

    # delete child reassign → root
    resp = await client.delete(
        f"/departments/{child_id}?mode=reassign&reassign_to_department_id={root_id}"
    )
    assert resp.status_code == 204

    # child удалён
    resp = await client.get(f"/departments/{child_id}")
    assert resp.status_code == 404

    # grandchild остался
    resp = await client.get(f"/departments/{grand_id}")
    assert resp.status_code == 200
