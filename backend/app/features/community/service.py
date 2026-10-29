from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.features.auth.models import User, utc_now
from app.features.community.models import CommunityPost
from app.features.community.schemas import PostCreate, PostUpdate, PostResponse


def post_response(post: CommunityPost) -> PostResponse:
    return PostResponse(
        id=post.id,
        user_id=post.user_id,
        author_name=post.user.display_name,
        content=post.content,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )

def get_posts(database: Session) -> list[PostResponse]:
    posts = database.scalars(
        select(CommunityPost)
        .options(joinedload(CommunityPost.user))
        .order_by(CommunityPost.created_at.desc(), CommunityPost.id.desc())
    ).all()

    return [post_response(post) for post in posts]

def create_post(
        database: Session, user: User, data: PostCreate
) -> PostResponse:
    post = CommunityPost(
        user_id=user.id,
        user=user,
        content=data.content,
    )
    database.add(post)
    database.commit()
    database.refresh(post)

    return post_response(post)

def update_post(
        database: Session, user: User, post_id: int, data: PostUpdate
) -> PostResponse:
    post = database.scalar(
        select(CommunityPost)
        .options(joinedload(CommunityPost.user))
        .where(
            CommunityPost.id == post_id,
            CommunityPost.user_id == user.id,
        )
    )

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    post.content = data.content
    post.updated_at = utc_now()

    database.commit()
    database.refresh(post)

    return post_response(post)

def delete_post(database: Session, user: User, post_id: int) -> None:
    post = database.scalar(
        select(CommunityPost).where(
            CommunityPost.id == post_id,
            CommunityPost.user_id == user.id,
        )
    )

    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    database.delete(post)
    database.commit()