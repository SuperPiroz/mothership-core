import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_search_incidents(async_client: AsyncClient, admin_headers: dict):
    """Test incident creation, search filtering, and lifecycle."""
    # 1. Create a service to associate incident with
    service_res = await async_client.post(
        "/api/v1/services",
        json={"name": "DNS Controller", "category": "system", "runtime": "k8s"},
        headers=admin_headers,
    )
    service_id = service_res.json()["id"]

    # 2. Create an incident
    incident_payload = {
        "title": "DNS resolution timeout on node",
        "description": "CoreDNS pods restarted unexpectedly causing temporary failure.",
        "severity": "high",
        "status": "investigating",
        "service_id": service_id,
    }
    create_res = await async_client.post("/api/v1/incidents", json=incident_payload)
    assert create_res.status_code == 201
    incident = create_res.json()
    assert incident["title"] == "DNS resolution timeout on node"
    assert incident["severity"] == "high"
    assert incident["status"] == "investigating"
    incident_id = incident["id"]

    # 3. Search by text (parameterized query test)
    search_res = await async_client.get("/api/v1/incidents?search=CoreDNS")
    assert search_res.status_code == 200
    search_items = search_res.json()
    assert len(search_items) >= 1
    assert any(item["id"] == incident_id for item in search_items)

    # 4. Resolve incident
    resolve_res = await async_client.put(
        f"/api/v1/incidents/{incident_id}",
        json={"status": "resolved", "resolution": "Scaled CoreDNS replica count to 2."},
    )
    assert resolve_res.status_code == 200
    resolved = resolve_res.json()
    assert resolved["status"] == "resolved"
    assert resolved["resolution"] == "Scaled CoreDNS replica count to 2."
    assert resolved["resolved_at"] is not None

    # 5. Delete incident
    del_res = await async_client.delete(f"/api/v1/incidents/{incident_id}")
    assert del_res.status_code == 204
