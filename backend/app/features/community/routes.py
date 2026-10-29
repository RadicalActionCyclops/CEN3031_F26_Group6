from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_csrf, require_verified_member
from app.features.auth.models import User
from app.features.community.schemas import PostCreate, PostUpdate, PostResponse
from app.features.community.service import (
    get_posts,
    create_post,
    update_post,
    delete_post,
)

router = APIRouter(
    prefix="/api/community/posts",
    tags=["community"],
    dependencies=[Depends(require_verified_member)]
)

Database = Annotated[Session, Depends(get_db)]
Member = Annotated[User, Depends(require_verified_member)]

@router.get("", response_model=list[PostResponse])
def list_posts(database: Database):
    return get_posts(database)


@router.post(
    "",
    response_model=PostResponse,
    status_code=201,
    dependencies=[Depends(require_csrf)],
)
def publish_post(data: PostCreate, database: Database, user: Member):
    return create_post(database, user, data)

@router.patch(
    "/{post_id}",
    response_model=PostResponse,
    dependencies=[Depends(require_csrf)],
)
def edit_post(post_id: int, data: PostUpdate, database: Database, user: Member):
    return update_post(database, user, post_id, data)

@router.delete(
    "/{post_id}",
    status_code=204,
    dependencies=[Depends(require_csrf)],
)
def remove_post(post_id: int, database: Database, user: Member):
    delete_post(database, user, post_id)