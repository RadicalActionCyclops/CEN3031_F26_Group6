from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_csrf, require_verified_member
from app.features.auth.models import AccountStatus, AffiliationStatus, User
from app.features.profiles.schemas import MemberSearchResponse, ProfileCreate, ProfileResponse, ProfileUpdate
from app.features.profiles.service import get_profile, profile_response, save_profile, search_members

router = APIRouter(prefix="/api/profiles", tags=["profiles"], dependencies=[Depends(require_verified_member)])
Database = Annotated[Session, Depends(get_db)]
Member = Annotated[User, Depends(require_verified_member)]


@router.get("/me", response_model=ProfileResponse)
def my_profile(database: Database, user: Member):
    return profile_response(get_profile(database, user.id))


@router.post("/me", response_model=ProfileResponse, status_code=201, dependencies=[Depends(require_csrf)])
def create_profile(data: ProfileCreate, database: Database, user: Member):
    return profile_response(save_profile(database, user, data, create=True))


@router.patch("/me", response_model=ProfileResponse, dependencies=[Depends(require_csrf)])
def update_profile(data: ProfileUpdate, database: Database, user: Member):
    return profile_response(save_profile(database, user, data, create=False))


@router.get("", response_model=MemberSearchResponse)
def members(
    database: Database,
    q: str = Query(default="", max_length=200),
    major: str = Query(default="", max_length=120),
    graduation_year: int | None = Query(default=None, ge=1900, le=2100),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
):
    return search_members(database, q.strip(), major.strip(), graduation_year, limit, offset)


@router.get("/{user_id}", response_model=ProfileResponse)
def member_profile(user_id: str, database: Database):
    profile = get_profile(database, user_id)
    user = profile.user
    if not user.email_verified or user.account_status != AccountStatus.ACTIVE or user.affiliation_status != AffiliationStatus.VERIFIED:
        raise HTTPException(404, "Profile not found")
    return profile_response(profile)
