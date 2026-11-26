from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(async_client: AsyncClient):
    """Test root endpoint returns service info."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "mothership-core"
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_healthz_liveness(async_client: AsyncClient):
    """Test healthz liveness probe returns ok."""
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mothership-core"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_readyz_healthy(async_client: AsyncClient):
    """Test readyz readiness probe returns ok when database is healthy."""
    with patch(
        "app.api.health.check_database_health",
        return_value=(True, "Database connection healthy"),
    ):
        response = await async_client.get("/readyz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"]["healthy"] is True


@pytest.mark.asyncio
async def test_readyz_unhealthy(async_client: AsyncClient):
    """Test readyz readiness probe returns 503 when database is unavailable."""
    with patch("app.api.health.check_database_health", return_value=(False, "Connection refused")):
        response = await async_client.get("/readyz")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"]["healthy"] is False


@pytest.mark.asyncio
async def test_security_headers_present(async_client: AsyncClient):
    """Verify that essential defensive security headers are attached to responses."""
    response = await async_client.get("/healthz")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "Strict-Transport-Security" in response.headers
