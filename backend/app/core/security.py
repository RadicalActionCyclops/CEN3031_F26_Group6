import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.features.auth.models import (
    AccountStatus,
    AffiliationStatus,
    AuthSession,
    User,
    UserRole,
)

password_hasher = PasswordHasher()
_development_secret = secrets.token_bytes(48)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def _secret_bytes(settings: Settings) -> bytes:
    if settings.secret_key is None:
        return _development_secret
    return settings.secret_key.get_secret_value().encode("utf-8")

def hash_token(token: str, settings: Settings) -> str:
    return hmac.new(
        _secret_bytes(settings), token.encode("utf-8"), hashlib.sha256
    ).hexdigest()

def set_session_cookies(
    response: Response,
    session_token: str,
    csrf_token: str,
    settings: Settings,
) -> None:
    max_age = settings.session_lifetime_minutes * 60
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
        max_age=max_age,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/api",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.secure_cookies,
        samesite=settings.cookie_samesite,
        path="/",
    )

def clear_session_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        path="/api",
        secure=settings.secure_cookies,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        path="/",
        secure=settings.secure_cookies,
        httponly=False,
        samesite=settings.cookie_samesite,
    )

def get_session_from_request(
    request: Request,
    database: Session,
    settings: Settings,
) -> AuthSession | None:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        return None
    session = database.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(raw_token, settings)
        )
    )
    if session is None or session.invalidated_at is not None:
        return None
    if as_utc(session.expires_at) <= utc_now():
        return None
    return session

def get_optional_current_user(
    request: Request,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    session = get_session_from_request(request, database, settings)
    if session is None:
        return None

    user = database.get(User, session.user_id)
    if user is None or user.account_status == AccountStatus.DISABLED:
        return None
    return user

def get_current_user(
    user: User | None = Depends(get_optional_current_user),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user

def require_csrf(
    request: Request,
    database: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _user: User = Depends(get_current_user),
) -> None:
    session = get_session_from_request(request, database, settings)
    csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
    csrf_header = request.headers.get("X-CSRF-Token")

    if (
        session is None
        or not csrf_cookie
        or not csrf_header
        or not secrets.compare_digest(csrf_cookie, csrf_header)
        or not secrets.compare_digest(
            session.csrf_token_hash, hash_token(csrf_header, settings)
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
        )

def require_verified_member(user: User = Depends(get_current_user)) -> User:
    if (
        not user.email_verified
        or user.account_status != AccountStatus.ACTIVE
        or user.affiliation_status != AffiliationStatus.VERIFIED
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified UF community membership is required",
        )
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access is required",
        )
    return user
