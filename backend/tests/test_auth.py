import json
from collections.abc import Generator
from dataclasses import dataclass
from datetime import timedelta

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import (
    Base,
    create_database_engine,
    create_session_factory,
    get_db,
)
from app.core.security import require_admin, require_verified_member, utc_now
from app.features.auth.models import AuthSession, EmailVerificationToken, User
from app.main import create_app


PASSWORD = "correct horse battery staple"


@dataclass
class AuthTestContext:
    client: TestClient
    session_factory: sessionmaker[Session]
    settings: Settings


@pytest.fixture
def auth_context(tmp_path) -> Generator[AuthTestContext, None, None]:
    database_path = tmp_path / "auth-test.sqlite3"
    outbox_path = tmp_path / "outbox.jsonl"
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{database_path}",
        secret_key="test-only-secret-that-is-not-used-outside-pytest",
        email_delivery="file",
        email_outbox_path=str(outbox_path),
    )
    database_engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(database_engine)
    Base.metadata.create_all(database_engine)
    application = create_app(settings=settings, database_engine=database_engine)

    def override_database() -> Generator[Session, None, None]:
        database = session_factory()
        try:
            yield database
        finally:
            database.close()

    application.dependency_overrides[get_db] = override_database
    application.dependency_overrides[get_settings] = lambda: settings

    @application.get("/api/_test/verified")
    def verified_only(_user: User = Depends(require_verified_member)) -> dict[str, bool]:
        return {"allowed": True}

    @application.get("/api/_test/admin")
    def admin_only(_user: User = Depends(require_admin)) -> dict[str, bool]:
        return {"allowed": True}

    with TestClient(application) as client:
        yield AuthTestContext(client, session_factory, settings)

    database_engine.dispose()


def registration_payload(email: str = "student@ufl.edu") -> dict[str, str]:
    return {
        "email": email,
        "display_name": "Test Student",
        "password": PASSWORD,
    }


def register(context: AuthTestContext, email: str = "student@ufl.edu"):
    return context.client.post("/api/auth/register", json=registration_payload(email))


def login(context: AuthTestContext, email: str = "student@ufl.edu"):
    return context.client.post(
        "/api/auth/login",
        json={"email": email, "password": PASSWORD},
    )


def verification_token(context: AuthTestContext, line_number: int = -1) -> str:
    outbox_lines = context.settings.email_outbox_path
    with open(outbox_lines, encoding="utf-8") as outbox:
        messages = [json.loads(line) for line in outbox if line.strip()]
    return messages[line_number]["verification_token"]


def test_successful_registration(auth_context: AuthTestContext) -> None:
    response = register(auth_context)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "student@ufl.edu"
    assert body["user"]["role"] == "member"
    assert body["user"]["email_verified"] is False
    assert body["user"]["affiliation_status"] == "unverified"
    assert "password" not in body["user"]


def test_invalid_email_format_is_rejected(auth_context: AuthTestContext) -> None:
    response = register(auth_context, "not-an-email")

    assert response.status_code == 422


def test_non_uf_student_email_is_rejected(auth_context: AuthTestContext) -> None:
    response = register(auth_context, "student@example.com")

    assert response.status_code == 422


def test_duplicate_email_is_rejected(auth_context: AuthTestContext) -> None:
    assert register(auth_context).status_code == 201

    duplicate = register(auth_context, "STUDENT@ufl.edu")

    assert duplicate.status_code == 409


def test_password_is_hashed(auth_context: AuthTestContext) -> None:
    assert register(auth_context).status_code == 201

    with auth_context.session_factory() as database:
        user = database.scalar(select(User).where(User.email == "student@ufl.edu"))
        assert user is not None
        assert user.password_hash != PASSWORD
        assert user.password_hash.startswith("$argon2id$")


def test_login_with_correct_credentials_creates_session(
    auth_context: AuthTestContext,
) -> None:
    register(auth_context)

    response = login(auth_context)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "student@ufl.edu"
    assert auth_context.settings.session_cookie_name in response.cookies
    assert auth_context.settings.csrf_cookie_name in response.cookies
    with auth_context.session_factory() as database:
        assert database.scalar(select(AuthSession)) is not None


def test_login_with_incorrect_credentials_is_rejected(
    auth_context: AuthTestContext,
) -> None:
    register(auth_context)

    response = auth_context.client.post(
        "/api/auth/login",
        json={"email": "student@ufl.edu", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_requires_authentication(auth_context: AuthTestContext) -> None:
    response = auth_context.client.get("/api/auth/me")

    assert response.status_code == 401


def test_logout_invalidates_session(auth_context: AuthTestContext) -> None:
    register(auth_context)
    assert login(auth_context).status_code == 200
    csrf_token = auth_context.client.cookies.get(
        auth_context.settings.csrf_cookie_name
    )

    response = auth_context.client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )

    assert response.status_code == 200
    assert auth_context.client.get("/api/auth/me").status_code == 401
    with auth_context.session_factory() as database:
        session = database.scalar(select(AuthSession))
        assert session is not None
        assert session.invalidated_at is not None


def test_verification_token_expiration_and_reuse(
    auth_context: AuthTestContext,
) -> None:
    register(auth_context, "expired@ufl.edu")
    expired_token = verification_token(auth_context)
    with auth_context.session_factory() as database:
        token_record = database.scalar(
            select(EmailVerificationToken).join(User).where(User.email == "expired@ufl.edu")
        )
        assert token_record is not None
        token_record.expires_at = utc_now() - timedelta(minutes=1)
        database.commit()

    expired_response = auth_context.client.post(
        "/api/auth/verify-email", json={"token": expired_token}
    )
    assert expired_response.status_code == 400

    register(auth_context, "reused@ufl.edu")
    reusable_token = verification_token(auth_context)
    first_use = auth_context.client.post(
        "/api/auth/verify-email", json={"token": reusable_token}
    )
    second_use = auth_context.client.post(
        "/api/auth/verify-email", json={"token": reusable_token}
    )

    assert first_use.status_code == 200
    assert first_use.json()["user"]["email_verified"] is True
    assert first_use.json()["user"]["affiliation_status"] == "unverified"
    assert second_use.status_code == 400


def test_unverified_user_cannot_access_verified_member_route(
    auth_context: AuthTestContext,
) -> None:
    register(auth_context)
    login(auth_context)

    response = auth_context.client.get("/api/_test/verified")

    assert response.status_code == 403


def test_member_cannot_access_administrative_route(
    auth_context: AuthTestContext,
) -> None:
    register(auth_context)
    login(auth_context)

    response = auth_context.client.get("/api/_test/admin")

    assert response.status_code == 403


def test_authenticated_write_requires_csrf(auth_context: AuthTestContext) -> None:
    register(auth_context)
    login(auth_context)

    without_header = auth_context.client.post("/api/auth/logout")
    assert without_header.status_code == 403

    csrf_token = auth_context.client.cookies.get(
        auth_context.settings.csrf_cookie_name
    )
    with_header = auth_context.client.post(
        "/api/auth/logout", headers={"X-CSRF-Token": csrf_token}
    )
    assert with_header.status_code == 200


def test_local_auth_is_unavailable_in_production(tmp_path) -> None:
    settings = Settings(
        environment="production",
        database_url=f"sqlite:///{tmp_path / 'production-test.sqlite3'}",
        secret_key="production-test-secret-with-at-least-32-characters",
        local_auth_enabled=True,
        email_delivery="file",
        email_outbox_path=str(tmp_path / "production-outbox.jsonl"),
    )
    database_engine: Engine = create_database_engine(settings.database_url)
    session_factory = create_session_factory(database_engine)
    application = create_app(settings=settings, database_engine=database_engine)

    def override_database() -> Generator[Session, None, None]:
        with session_factory() as database:
            yield database

    application.dependency_overrides[get_db] = override_database
    application.dependency_overrides[get_settings] = lambda: settings

    with TestClient(application) as client:
        response = client.post(
            "/api/auth/register",
            json=registration_payload("production@ufl.edu"),
        )

    assert response.status_code == 503
    database_engine.dispose()
