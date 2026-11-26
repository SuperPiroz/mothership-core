import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_get_service(async_client: AsyncClient, admin_headers: dict):
    """Test creating a new service in the catalog and retrieving it."""
    payload = {
        "name": "Hermes Agent",
        "category": "ai",
        "runtime": "docker",
        "description": "Nous Research autonomous agent",
        "internal_url": "http://127.0.0.1:9119",
        "public_url": "https://hermes.pydev.se",
        "tags": "ai,llm,agent",
        "is_monitored": True,
    }
    response = await async_client.post("/api/v1/services", json=payload, headers=admin_headers)
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Hermes Agent"
    assert created["slug"] == "hermes-agent"
    assert created["category"] == "ai"
    service_id = created["id"]

    # Retrieve by ID (public/open)
    get_res = await async_client.get(f"/api/v1/services/{service_id}")
    assert get_res.status_code == 200
    assert get_res.json()["slug"] == "hermes-agent"

    # List services (public/open)
    list_res = await async_client.get("/api/v1/services?category=ai")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(item["id"] == service_id for item in items)


@pytest.mark.asyncio
async def test_service_duplicate_slug_conflict(async_client: AsyncClient, admin_headers: dict):
    """Test that creating a service with duplicate slug returns 409 Conflict."""
    payload = {
        "name": "PostgreSQL Primary",
        "category": "database",
        "runtime": "docker",
    }
    res1 = await async_client.post("/api/v1/services", json=payload, headers=admin_headers)
    assert res1.status_code == 201

    res2 = await async_client.post("/api/v1/services", json=payload, headers=admin_headers)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_update_and_delete_service(async_client: AsyncClient, admin_headers: dict):
    """Test updating service metadata and deleting it."""
    payload = {
        "name": "Old Service",
        "category": "web",
        "runtime": "docker",
    }
    create_res = await async_client.post("/api/v1/services", json=payload, headers=admin_headers)
    assert create_res.status_code == 201
    service_id = create_res.json()["id"]

    # Update (requires admin)
    update_res = await async_client.put(
        f"/api/v1/services/{service_id}",
        json={"name": "Updated Service", "is_monitored": False},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Service"
    assert update_res.json()["slug"] == "updated-service"
    assert update_res.json()["is_monitored"] is False

    # Delete (requires admin)
    del_res = await async_client.delete(f"/api/v1/services/{service_id}", headers=admin_headers)
    assert del_res.status_code == 204

    # Verify 404
    verify_res = await async_client.get(f"/api/v1/services/{service_id}")
    assert verify_res.status_code == 404
