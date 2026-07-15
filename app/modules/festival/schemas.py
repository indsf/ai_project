# app/modules/festival/schemas.py

from typing import List, Optional

from pydantic import BaseModel


class FestivalListItem(BaseModel):
    content_id: str
    title: str
    addr1: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class FestivalListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[FestivalListItem]


class FestivalDetail(BaseModel):
    content_id: str
    title: str
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    tel: Optional[str] = None
    mapx: Optional[float] = None
    mapy: Optional[float] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    region: Optional[str] = None

    class Config:
        from_attributes = True


class FestivalSeedResponse(BaseModel):
    message: str
    count: int