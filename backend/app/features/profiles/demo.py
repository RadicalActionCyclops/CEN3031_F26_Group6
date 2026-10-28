"""Create explicitly synthetic members for a local Sprint 1 demonstration."""
import secrets

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal, initialize_database
from app.core.security import hash_password, utc_now
from app.features.auth.models import AccountStatus, AffiliationStatus, AffiliationType, User
from app.features.profiles.models import Profile


def main():
    settings = get_settings()
    if settings.environment != "development" or not settings.development_auth_available:
        raise SystemExit("Demo accounts may only be created with local authentication in development.")
    if not settings.database_url.startswith("sqlite:"):
        raise SystemExit("Demo accounts require a local development SQLite database.")
    initialize_database()
    accounts = [
        ("profiles.student.demo@ufl.edu", "Alex Demo", AffiliationType.STUDENT, None, ""),
        ("profiles.alumni.demo@ufl.edu", "Jordan Demo", AffiliationType.ALUMNI, 2022, "Computer Science"),
        ("profiles.finance.demo@ufl.edu", "Taylor Demo", AffiliationType.STUDENT, 2027, "Finance"),
    ]
    with SessionLocal() as database:
        if database.scalar(select(User).where(User.email.in_([a[0] for a in accounts]))):
            raise SystemExit("Demo accounts already exist. Existing accounts and passwords were left unchanged.")
        password = secrets.token_urlsafe(18)
        for email, name, affiliation, year, major in accounts:
            user = User(
                email=email, display_name=name, affiliation=affiliation,
                password_hash=hash_password(password), email_verified=True,
                email_verified_at=utc_now(), account_status=AccountStatus.ACTIVE,
                affiliation_status=AffiliationStatus.VERIFIED,
            )
            database.add(user)
            database.flush()
            if year:
                database.add(Profile(user_id=user.id, graduation_year=year, major=major))
        database.commit()
    print("Synthetic local demo accounts only; no real UF affiliation was verified.")
    for account in accounts:
        print(account[0])
    print(f"Shared demo password: {password}")
    print("Alex starts without a profile so you can demonstrate profile setup.")


if __name__ == "__main__":
    main()
