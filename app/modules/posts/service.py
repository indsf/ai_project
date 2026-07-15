# app/modules/posts/service.py
# 다른 모듈(recommend 등)에 노출할 함수만 여기에 정의한다.
# 다른 모듈에서 posts.crud / posts.models 를 직접 import 하는 것은 금지.

from datetime import date as date_type
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.posts import crud
from app.modules.posts.models import Post


class PostSummary:
    """recommend 모듈 등 외부에 노출하는 요약 DTO. Post ORM 객체를 그대로 넘기지 않기 위함."""

    def __init__(self, post: Post):
        self.id = post.id
        self.title = post.title
        self.category = post.category
        self.indoor_outdoor = post.indoor_outdoor
        self.location = post.location
        self.start_date = post.start_date
        self.end_date = post.end_date


def get_posts_for_recommendation(
    db: Session, category: Optional[str] = None
) -> list[PostSummary]:
    """recommend 모듈이 호출하는 공개 인터페이스."""
    posts = crud.list_for_recommendation(db, category)
    return [PostSummary(p) for p in posts]


def get_post_context_for_chat(db: Session, limit: int = 15) -> list[PostSummary]:
    """챗봇이 참고할 진행 중인 축제/관광지 컨텍스트."""
    posts = crud.list_for_chat_context(db, date_type.today(), limit)
    return [PostSummary(p) for p in posts]
