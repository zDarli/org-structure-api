import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_create_department(client: AsyncClient) -> None:
    # create root department
    resp = await client.post("/departments/", json={"name": "HQ", "parent_id": None})
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert isinstance(data["id"], int)
    assert data["name"] == "HQ"
    assert data["parent_id"] is None

    # uniqueness внутри одного parent: создаём второй раз то же самое
    resp2 = await client.post("/departments/", json={"name": "HQ", "parent_id": None})
    assert resp2.status_code == 409, resp2.text
