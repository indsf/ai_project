# app/modules/posts/crud.py

from datetime import date as date_type
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.posts import schemas
from app.modules.posts.models import Post


def get_post(db: Session, post_id: int) -> Optional[Post]:
    return db.query(Post).filter(Post.id == post_id).first()


def list_posts(
    db: Session,
    category: Optional[str],
    search: Optional[str],
    page: int,
    size: int,
):
    query = db.query(Post)

    if category:
        query = query.filter(Post.category == category)

    if search:
        query = query.filter(Post.title.contains(search))

    total = query.count()

    items = (
        query.order_by(Post.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return total, items


def create_post(db: Session, data: schemas.PostCreate) -> Post:
    payload = data.model_dump()

    if payload["category"] == "spot":
        payload["start_date"] = None
        payload["end_date"] = None

    post = Post(**payload)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def increment_view_count(db: Session, post: Post) -> Post:
    post.view_count += 1
    db.commit()
    db.refresh(post)
    return post


def update_post(db: Session, post: Post, data: schemas.PostUpdate) -> Post:
    payload = data.model_dump(exclude={"password"})

    if payload["category"] == "spot":
        payload["start_date"] = None
        payload["end_date"] = None

    for field, value in payload.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post: Post) -> None:
    db.delete(post)
    db.commit()


def list_for_recommendation(db: Session, category: Optional[str]):
    """recommend 모듈이 날씨 기반 추천을 만들 때 사용하는 조회 함수."""
    query = db.query(Post)

    if category:
        query = query.filter(Post.category == category)

    return query.all()


def list_for_chat_context(db: Session, today: date_type, limit: int = 15):
    """챗봇이 참고할 진행 중인 축제/관광지 컨텍스트."""
    return (
        db.query(Post)
        .filter(
            or_(
                Post.category == "spot",
                Post.end_date >= today,
                Post.end_date.is_(None),
            )
        )
        .limit(limit)
        .all()
    )
