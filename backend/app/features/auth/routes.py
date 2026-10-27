from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.security import (
    clear_session_cookies,
    get_current_user,
    get_optional_current_user,
    require_admin,
    require_csrf,
    require_verified_member,
    set_session_cookies,
)
from app.features.auth.models import User
from app.features.auth.schemas import (
    AuthenticationError,
    AuthenticationStatus,
    CurrentUserResponse,
    DetailResponse,
    EmailVerificationRequest,
    EmailVerificationResponse,
    LoginRequest,
    LoginResponse,
    RegistrationResponse,
    UserRegistration,
)
from app.features.auth.service import (
    invalidate_session,
    login_user,
    register_user,
    verify_email_token,
)


router = APIRouter(prefix="/api/auth", tags=["authentication"])

AUTH_ERROR_RESPONSES = {
    401: {"model": AuthenticationError},
    403: {"model": AuthenticationError},
}


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": AuthenticationError}},
)
def register(
    registration: UserRegistration,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RegistrationResponse:
    result = register_user(database, registration, settings)
    return RegistrationResponse(
        detail="Account created. Check the development email outbox to verify your email.",
        verification_delivery=settings.email_delivery,
        user=result.user,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    responses=AUTH_ERROR_RESPONSES,
)
def login(
    credentials: LoginRequest,
    response: Response,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    result = login_user(database, credentials, settings)
    set_session_cookies(
        response,
        result.session_token,
        result.csrf_token,
        settings,
    )
    return LoginResponse(detail="Login successful", user=result.user)


@router.post(
    "/logout",
    response_model=DetailResponse,
    dependencies=[Depends(require_csrf)],
    responses=AUTH_ERROR_RESPONSES,
)
def logout(
    request: Request,
    response: Response,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> DetailResponse:
    invalidate_session(
        database,
        request.cookies.get(settings.session_cookie_name),
        settings,
    )
    clear_session_cookies(response, settings)
    return DetailResponse(detail="Logout successful")


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    responses={401: {"model": AuthenticationError}},
)
def current_user(user: User = Depends(get_current_user)) -> User:
    return user


@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
    responses={400: {"model": AuthenticationError}},
)
def verify_email(
    verification: EmailVerificationRequest,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> EmailVerificationResponse:
    user = verify_email_token(database, verification.token, settings)
    return EmailVerificationResponse(
        detail=(
            "Email ownership verified. UF affiliation remains unverified until an "
            "approved identity process confirms it."
        ),
        user=user,
    )


@router.get("/status", response_model=AuthenticationStatus)
def authentication_status(
    user: User | None = Depends(get_optional_current_user),
    settings: Settings = Depends(get_settings),
) -> AuthenticationStatus:
    return AuthenticationStatus(
        authenticated=user is not None,
        local_auth_enabled=settings.development_auth_available,
        user=user,
    )


__all__ = [
    "get_current_user",
    "require_admin",
    "require_verified_member",
    "router",
]
