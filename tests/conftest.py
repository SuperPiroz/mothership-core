import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models  # noqa: F401
from app.config import get_settings
from app.database import Base, get_db
from app.main import app
from app.services.auth_service import seed_initial_admin

settings = get_settings()

# Use NullPool for tests so asyncpg connections are never pooled across closed event loops
test_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def clean_database():
    """Ensure clean schema and isolated test state for every test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        await seed_initial_admin(session)
    yield


@pytest.fixture
async def async_client():
    """Async HTTP client fixture for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def admin_headers(async_client: AsyncClient):
    """Fixture that logs in as initial admin and returns Authorization bearer header."""
    res = await async_client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.ADMIN_INITIAL_USERNAME,
            "password": settings.ADMIN_INITIAL_PASSWORD,
        },
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
