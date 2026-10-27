import json
import logging
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import (
    as_utc,
    generate_token,
    hash_password,
    hash_token,
    utc_now,
    verify_password,
)
from app.features.auth.models import (
    AccountStatus,
    AuthSession,
    EmailVerificationToken,
    User,
)
from app.features.auth.schemas import LoginRequest, UserRegistration


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegistrationResult:
    user: User
    verification_token: str


@dataclass(frozen=True)
class SessionResult:
    user: User
    session_token: str
    csrf_token: str


def ensure_development_auth_available(settings: Settings) -> None:
    if not settings.development_auth_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Local development authentication is unavailable",
        )


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_user(
    database: Session,
    registration: UserRegistration,
    settings: Settings,
) -> RegistrationResult:
    ensure_development_auth_available(settings)
    email = normalize_email(str(registration.email))

    existing_user = database.scalar(select(User).where(User.email == email))
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=email,
        display_name=registration.display_name,
        password_hash=hash_password(registration.password),
    )
    database.add(user)
    try:
        database.flush()
    except IntegrityError as exc:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc

    raw_token = generate_token()
    verification = EmailVerificationToken(
        user_id=user.id,
        token_hash=hash_token(raw_token, settings),
        expires_at=utc_now()
        + timedelta(minutes=settings.verification_token_lifetime_minutes),
    )
    database.add(verification)
    database.commit()
    database.refresh(user)

    deliver_verification_email(user.email, raw_token, settings)
    return RegistrationResult(user=user, verification_token=raw_token)


def deliver_verification_email(email: str, token: str, settings: Settings) -> None:
    message = {
        "to": email,
        "subject": "Verify your SwampSpace email",
        "verification_token": token,
        "verification_path": "/api/auth/verify-email",
    }

    if settings.email_delivery == "file":
        outbox = Path(settings.email_outbox_path)
        outbox.parent.mkdir(parents=True, exist_ok=True)
        with outbox.open("a", encoding="utf-8") as outbox_file:
            outbox_file.write(json.dumps(message) + "\n")
        return

    logger.warning("Development verification message: %s", json.dumps(message))


def authenticate_user(
    database: Session,
    login: LoginRequest,
    settings: Settings,
) -> User:
    ensure_development_auth_available(settings)
    email = normalize_email(str(login.email))
    user = database.scalar(select(User).where(User.email == email))

    if user is None or not verify_password(login.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user.account_status == AccountStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is disabled",
        )
    return user


def create_session(
    database: Session,
    user: User,
    settings: Settings,
) -> SessionResult:
    session_token = generate_token()
    csrf_token = generate_token()
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(session_token, settings),
        csrf_token_hash=hash_token(csrf_token, settings),
        expires_at=utc_now() + timedelta(minutes=settings.session_lifetime_minutes),
    )
    database.add(session)
    database.commit()
    return SessionResult(
        user=user,
        session_token=session_token,
        csrf_token=csrf_token,
    )


def login_user(
    database: Session,
    login: LoginRequest,
    settings: Settings,
) -> SessionResult:
    user = authenticate_user(database, login, settings)
    return create_session(database, user, settings)


def invalidate_session(
    database: Session,
    raw_session_token: str | None,
    settings: Settings,
) -> None:
    if not raw_session_token:
        return
    session = database.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(raw_session_token, settings)
        )
    )
    if session is not None and session.invalidated_at is None:
        session.invalidated_at = utc_now()
        database.commit()


def verify_email_token(
    database: Session,
    raw_token: str,
    settings: Settings,
) -> User:
    ensure_development_auth_available(settings)
    token = database.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_token(raw_token, settings)
        )
    )
    if (
        token is None
        or token.used_at is not None
        or as_utc(token.expires_at) <= utc_now()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid or expired",
        )

    user = database.get(User, token.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid or expired",
        )

    now = utc_now()
    token.used_at = now
    user.email_verified = True
    user.email_verified_at = now
    user.account_status = AccountStatus.ACTIVE
    database.commit()
    database.refresh(user)
    return user
