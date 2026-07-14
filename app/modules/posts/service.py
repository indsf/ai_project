from datetime import date as date_type
from typing import Optional
from sqlalchemy.orm import Session
from app.modules.posts import crud
from app.modules.posts.models import Post


class PostSummary:
    """recommend 모듈에 노출하는 요약 DTO. Post ORM 객체를 외부로 직접 넘기지 않기 위함."""

    def __init__(self, post: Post):
        self.id = post.id
        self.title = post.title
        self.category = post.category
        self.indoor_outdoor = post.indoor_outdoor
        self.location = post.location
        self.start_date = post.start_date
        self.end_date = post.end_date


def get_posts_for_recommendation(db: Session, category: Optional[str] = None) -> list[PostSummary]:
    """recommend 모듈이 호출하는 공개 인터페이스. posts.crud/posts.models 직접 import 금지."""
    posts = crud.list_for_recommendation(db, category)
    return [PostSummary(p) for p in posts]


def get_post_context_for_chat(db: Session, limit: int = 15) -> list[PostSummary]:
    """챗봇이 참고할 축제/관광지 컨텍스트. recommend.chat_service에서 사용."""
    posts = crud.list_for_chat_context(db, date_type.today(), limit)
    return [PostSummary(p) for p in posts]
