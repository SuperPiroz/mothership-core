import pytest
from httpx import AsyncClient

from app.config import get_settings

settings = get_settings()


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """Test successful authentication returns a valid JWT access token."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.ADMIN_INITIAL_USERNAME,
            "password": settings.ADMIN_INITIAL_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(async_client: AsyncClient):
    """Test invalid credentials return 401 Unauthorized."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.ADMIN_INITIAL_USERNAME,
            "password": "wrong-password",
        },
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_profile(async_client: AsyncClient):
    """Test retrieving authenticated user profile via /me."""
    # 1. Login to get token
    login_res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.ADMIN_INITIAL_USERNAME,
            "password": settings.ADMIN_INITIAL_PASSWORD,
        },
    )
    token = login_res.json()["access_token"]

    # 2. Call /me with Bearer token
    me_res = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    user = me_res.json()
    assert user["username"] == settings.ADMIN_INITIAL_USERNAME
    assert user["role"] == "admin"


@pytest.mark.asyncio
async def test_role_based_access_control_viewer_forbidden(async_client: AsyncClient):
    """Test that a viewer role is forbidden (403) from creating services."""
    # 1. Login as admin
    admin_login = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.ADMIN_INITIAL_USERNAME,
            "password": settings.ADMIN_INITIAL_PASSWORD,
        },
    )
    admin_token = admin_login.json()["access_token"]

    # 2. Admin creates a viewer user
    create_viewer = await async_client.post(
        "/api/v1/auth/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "vieweruser",
            "password": "viewerpassword123",
            "role": "viewer",
        },
    )
    assert create_viewer.status_code == 201

    # 3. Login as viewer
    viewer_login = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": "vieweruser",
            "password": "viewerpassword123",
        },
    )
    viewer_token = viewer_login.json()["access_token"]

    # 4. Viewer attempts to register a service -> Must return 403 Forbidden
    forbidden_res = await async_client.post(
        "/api/v1/services",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "Hacked Service", "category": "web"},
    )
    assert forbidden_res.status_code == 403
    assert "administrator privileges required" in forbidden_res.json()["detail"]

    # 5. Viewer can still read services (GET is permitted)
    read_res = await async_client.get(
        "/api/v1/services",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert read_res.status_code == 200
