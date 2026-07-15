# app/modules/posts/models.py
# 커뮤니티 게시판 테이블 정의

from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func

from app.core.database import Base


class Post(Base):
    """
    커뮤니티 게시글.
    category로 축제(festival) / 관광지(spot) / 맛집(food) 글을 함께 관리한다.
    """

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String, nullable=False)          # festival | spot | food
    indoor_outdoor = Column(String, nullable=False)     # indoor | outdoor | both
    location = Column(String(200), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    password = Column(String, nullable=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
