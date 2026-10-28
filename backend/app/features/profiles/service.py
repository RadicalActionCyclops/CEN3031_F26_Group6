from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.features.auth.models import AccountStatus, AffiliationStatus, User
from app.features.profiles.models import Profile
from app.features.profiles.schemas import ProfileCreate, ProfileResponse, ProfileUpdate
from app.core.security import utc_now


def profile_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        user_id=profile.user_id,
        full_name=profile.user.display_name,
        status=profile.user.affiliation,
        graduation_year=profile.graduation_year,
        major=profile.major,
        updated_at=profile.updated_at,
    )


def get_profile(database: Session, user_id: str) -> Profile:
    profile = database.scalar(
        select(Profile).options(joinedload(Profile.user)).where(Profile.user_id == user_id)
    )
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile


def save_profile(
    database: Session, user: User, data: ProfileCreate | ProfileUpdate, *, create: bool
) -> Profile:
    profile = database.get(Profile, user.id)
    if create and profile is not None:
        raise HTTPException(409, "You already have a profile")
    if not create and profile is None:
        raise HTTPException(404, "Create your profile first")
    values = data.model_dump(exclude_unset=not create)
    if profile is None:
        profile = Profile(user_id=user.id, user=user)
        database.add(profile)
    if "full_name" in values:
        user.display_name = values.pop("full_name")
    if "status" in values:
        # Self-described status does not change verified membership.
        user.affiliation = values.pop("status")
    for field, value in values.items():
        setattr(profile, field, value)
    profile.updated_at = utc_now()
    database.commit()
    database.refresh(profile)
    return profile


def visible_members():
    return (
        User.email_verified.is_(True),
        User.account_status == AccountStatus.ACTIVE,
        User.affiliation_status == AffiliationStatus.VERIFIED,
    )


def search_members(database: Session, q: str, major: str, year: int | None, limit: int, offset: int):
    statement = select(Profile).join(Profile.user).where(*visible_members())
    for word in q.split():
        statement = statement.where(or_(
            User.display_name.icontains(word, autoescape=True),
            Profile.major.icontains(word, autoescape=True),
        ))
    if major:
        statement = statement.where(func.lower(Profile.major) == major.lower())
    if year is not None:
        statement = statement.where(Profile.graduation_year == year)
    total = database.scalar(select(func.count()).select_from(statement.subquery()))
    profiles = database.scalars(
        statement.options(joinedload(Profile.user))
        .order_by(func.lower(User.display_name), Profile.user_id).limit(limit).offset(offset)
    ).all()
    return {"items": [profile_response(p) for p in profiles], "total": total, "limit": limit, "offset": offset}
