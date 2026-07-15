# app/modules/posts/schemas.py

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PostCategory(str, Enum):
    """게시글 카테고리. Swagger에서 드롭다운으로 뜬다."""

    festival = "festival"  # 축제 후기/정보
    spot = "spot"          # 관광지/명소 추천
    food = "food"          # 맛집 추천


class IndoorOutdoor(str, Enum):
    """실내/실외 여부."""

    indoor = "indoor"
    outdoor = "outdoor"
    both = "both"


class PostBase(BaseModel):
    title: str = Field(..., examples=["구미라면축제 다녀왔어요"])
    content: str = Field(..., examples=["진짜 맛있었어요 강추합니다"])
    category: PostCategory = Field(..., examples=[PostCategory.festival])
    indoor_outdoor: IndoorOutdoor = Field(..., examples=[IndoorOutdoor.outdoor])
    location: Optional[str] = Field(None, examples=["구미역"])
    start_date: Optional[date] = Field(
        None, description="축제/행사 시작일. category=spot(관광지)이면 무시됨", examples=["2026-07-10"]
    )
    end_date: Optional[date] = Field(None, examples=["2026-07-13"])


class PostCreate(PostBase):
    password: str = Field(..., description="게시글 수정/삭제할 때 필요한 비밀번호", examples=["1234"])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "구미라면축제 다녀왔어요",
                "content": "진짜 맛있었어요 강추합니다",
                "category": "festival",
                "indoor_outdoor": "outdoor",
                "location": "구미역",
                "start_date": "2026-07-10",
                "end_date": "2026-07-13",
                "password": "1234",
            }
        }


class PostUpdate(PostBase):
    password: str = Field(..., description="글 작성 시 등록한 비밀번호", examples=["1234"])

    class Config:
        json_schema_extra = {
            "example": {
                "title": "구미라면축제 다녀왔어요 (수정)",
                "content": "다시 가고 싶을 정도로 맛있었어요",
                "category": "festival",
                "indoor_outdoor": "outdoor",
                "location": "구미역",
                "start_date": "2026-07-10",
                "end_date": "2026-07-13",
                "password": "1234",
            }
        }


class PostDeleteRequest(BaseModel):
    password: str = Field(..., examples=["1234"])


class PostListItem(BaseModel):
    id: int = Field(..., examples=[1])
    title: str = Field(..., examples=["구미라면축제 다녀왔어요"])
    category: PostCategory
    indoor_outdoor: IndoorOutdoor
    location: Optional[str] = Field(None, examples=["구미역"])
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    view_count: int = Field(..., examples=[12])
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "구미라면축제 다녀왔어요",
                "category": "festival",
                "indoor_outdoor": "outdoor",
                "location": "구미역",
                "start_date": "2026-07-10",
                "end_date": "2026-07-13",
                "view_count": 12,
                "created_at": "2026-07-15T09:00:00",
            }
        }


class PostListResponse(BaseModel):
    total: int = Field(..., examples=[1])
    page: int = Field(..., examples=[1])
    size: int = Field(..., examples=[10])
    items: List[PostListItem]


class PostDetail(BaseModel):
    id: int = Field(..., examples=[1])
    title: str = Field(..., examples=["구미라면축제 다녀왔어요"])
    content: str = Field(..., examples=["진짜 맛있었어요 강추합니다"])
    category: PostCategory
    indoor_outdoor: IndoorOutdoor
    location: Optional[str] = Field(None, examples=["구미역"])
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    view_count: int = Field(..., examples=[13])
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "구미라면축제 다녀왔어요",
                "content": "진짜 맛있었어요 강추합니다",
                "category": "festival",
                "indoor_outdoor": "outdoor",
                "location": "구미역",
                "start_date": "2026-07-10",
                "end_date": "2026-07-13",
                "view_count": 13,
                "created_at": "2026-07-15T09:00:00",
                "updated_at": None,
            }
        }


class PostCreateResponse(BaseModel):
    id: int = Field(..., examples=[1])
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {"id": 1, "created_at": "2026-07-15T09:00:00"}
        }


class PostUpdateResponse(BaseModel):
    id: int = Field(..., examples=[1])
    updated_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {"id": 1, "updated_at": "2026-07-15T09:30:00"}
        }
