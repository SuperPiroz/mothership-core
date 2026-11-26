import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.health import router as health_router
from app.api.v1 import api_v1_router
from app.config import get_settings
from app.database import init_db

settings = get_settings()

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mothership.core")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces essential defensive HTTP security headers on all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown procedures."""
    logger.info(
        "Starting up %s v%s in %s environment",
        settings.PROJECT_NAME,
        __version__,
        settings.ENVIRONMENT,
    )
    # Ensure database tables exist in development / test
    if settings.ENVIRONMENT != "production":
        try:
            await init_db()
            logger.info("Database schema initialized successfully")
        except Exception as exc:
            logger.warning("Could not auto-initialize DB schema on startup: %s", exc)
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


app = FastAPI(
    title="Mothership Core API",
    description="Central backend service for Mothership Dashboard platform",
    version=__version__,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router)
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": __version__,
        "status": "running",
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "disabled in production",
    }
