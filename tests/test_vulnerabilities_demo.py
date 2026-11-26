import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_demonstrate_sql_injection_vulnerability_and_fix(
    async_client: AsyncClient,
    admin_headers: dict,
):
    """
    OWASP A03:2021 - Injection Demonstration.
    Shows exploitation of raw string concatenation vs secure parameterized queries.
    """
    # 1. Create two test incidents
    await async_client.post(
        "/api/v1/incidents",
        headers=admin_headers,
        json={
            "title": "Secret Security Breach Investigation",
            "description": "Internal classified incident details.",
            "severity": "critical",
        },
    )
    await async_client.post(
        "/api/v1/incidents",
        headers=admin_headers,
        json={
            "title": "Routine Disk Maintenance",
            "description": "Routine log rotation completed.",
            "severity": "low",
        },
    )

    # 2. Test vulnerable endpoint with non-matching string -> returns 0
    clean_res = await async_client.get(
        "/api/v1/incidents/demo/vulnerable-search?q=NonExistentTermXYZ",
    )
    assert clean_res.status_code == 200
    assert len(clean_res.json()) == 0

    # 3. EXPLOITATION: Inject classic SQL injection comment payload: ' OR 1=1 --
    # Raw SQL becomes: WHERE title LIKE '%test' OR 1=1 -- %'
    sqli_payload = "test' OR 1=1 -- "
    sqli_res = await async_client.get(
        f"/api/v1/incidents/demo/vulnerable-search?q={sqli_payload}",
    )
    assert sqli_res.status_code == 200
    exploited_data = sqli_res.json()
    # SQLi successfully bypassed the filter and returned ALL database rows!
    assert len(exploited_data) >= 2
    titles = [item["title"] for item in exploited_data]
    assert "Secret Security Breach Investigation" in titles
    assert "Routine Disk Maintenance" in titles

    # 4. VERIFICATION OF FIX: Test secure parameterized search endpoint with same payload
    secure_res = await async_client.get(
        f"/api/v1/incidents?search={sqli_payload}",
    )
    assert secure_res.status_code == 200
    # Secure parameterized query treats the payload literally -> returns 0 rows!
    assert len(secure_res.json()) == 0


@pytest.mark.asyncio
async def test_demonstrate_broken_access_control_and_fix(
    async_client: AsyncClient,
    admin_headers: dict,
):
    """
    OWASP A01:2021 - Broken Access Control / IDOR Demonstration.
    Shows unauthorized deletion via insecure endpoint vs enforcement of RBAC.
    """
    # 1. Create an incident
    incident_res = await async_client.post(
        "/api/v1/incidents",
        headers=admin_headers,
        json={
            "title": "Production Server Outage",
            "description": "Database connection pool saturated.",
            "severity": "high",
        },
    )
    assert incident_res.status_code == 201
    incident_id = incident_res.json()["id"]

    # 2. EXPLOITATION: Anonymous attacker deletes incident without any auth header
    idor_res = await async_client.delete(
        f"/api/v1/incidents/demo/insecure-delete/{incident_id}",
    )
    assert idor_res.status_code == 200
    assert "without authorization check" in idor_res.json()["message"]

    # Verify incident was deleted
    verify_deleted = await async_client.get(f"/api/v1/incidents/{incident_id}")
    assert verify_deleted.status_code == 404

    # 3. VERIFICATION OF FIX: Creating and protecting services with RBAC
    # Viewer tries to delete protected resource -> 403 Forbidden or 401 Unauthorized
    srv_res = await async_client.post(
        "/api/v1/services",
        headers=admin_headers,
        json={"name": "Protected Gateway", "category": "system"},
    )
    srv_id = srv_res.json()["id"]

    unauth_delete = await async_client.delete(f"/api/v1/services/{srv_id}")
    # Fix verification: Unauthenticated requests are rejected
    assert unauth_delete.status_code == 401
