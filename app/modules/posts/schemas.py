from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class PostBase(BaseModel):
    title: str
    content: str
    category: str
    indoor_outdoor: str
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class PostCreate(PostBase):
    password: str


class PostUpdate(PostBase):
    password: str


class PostDeleteRequest(BaseModel):
    password: str


class PostListItem(BaseModel):
    id: int
    title: str
    category: str
    indoor_outdoor: str
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    view_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class PostListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[PostListItem]


class PostDetail(BaseModel):
    id: int
    title: str
    content: str
    category: str
    indoor_outdoor: str
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostCreateResponse(BaseModel):
    id: int
    created_at: datetime


class PostUpdateResponse(BaseModel):
    id: int
    updated_at: Optional[datetime] = None
