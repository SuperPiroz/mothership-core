import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger("mothership.core.auth")


class LoginJSONRequest(BaseModel):
    username: str
    password: str


@router.post(
    "/login",
    response_model=Token,
    summary="User Login (JSON body)",
)
async def login_json(
    credentials: LoginJSONRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with username and password, returning a signed JWT access token."""
    user = await auth_service.authenticate_user(
        db,
        username=credentials.username,
        password=credentials.password,
    )
    if not user:
        logger.warning("Failed login attempt for username: '%s'", credentials.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("Successful login for user '%s' (role '%s')", user.username, user.role)
    token = auth_service.create_access_token(
        subject=user.username,
        role=user.role,
    )
    return Token(access_token=token, token_type="bearer")


@router.post(
    "/token",
    response_model=Token,
    summary="OAuth2 Form Login (for Swagger UI)",
    include_in_schema=False,
)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 compatible token login for interactive API documentation."""
    user = await auth_service.authenticate_user(
        db,
        username=form_data.username,
        password=form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_service.create_access_token(
        subject=user.username,
        role=user.role,
    )
    return Token(access_token=token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve details and role for currently authenticated user."""
    return current_user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Admin only)",
)
async def register_user(
    user_in: UserCreate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account. Requires administrator privileges."""
    existing = await auth_service.get_user_by_username(db, user_in.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with username '{user_in.username}' already exists",
        )
    logger.info(
        "Admin '%s' created new user '%s' with role '%s'",
        current_admin.username,
        user_in.username,
        user_in.role,
    )
    return await auth_service.create_user(db, user_in)
