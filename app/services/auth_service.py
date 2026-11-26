import logging
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.schemas.user import UserCreate

settings = get_settings()
logger = logging.getLogger("mothership.core.auth")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.warning("Password verification failed unexpectedly: %s", exc)
        return False


def create_access_token(
    subject: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT access token containing subject and role."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": expire,
        "iss": "mothership-core",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a signed JWT token."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer="mothership-core",
    )


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Query a user by username."""
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> User | None:
    """Verify credentials and return user if valid."""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a new user with hashed password."""
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,
        is_active=True,
    )
    db.add(db_user)
    await db.flush()
    await db.refresh(db_user)
    return db_user


async def seed_initial_admin(db: AsyncSession) -> User | None:
    """Ensure at least one admin account exists on initial startup."""
    admin = await get_user_by_username(db, settings.ADMIN_INITIAL_USERNAME)
    if not admin:
        logger.info(
            "Creating initial admin account: '%s'",
            settings.ADMIN_INITIAL_USERNAME,
        )
        admin = User(
            username=settings.ADMIN_INITIAL_USERNAME,
            email=None,
            hashed_password=hash_password(settings.ADMIN_INITIAL_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        return admin
    return admin
