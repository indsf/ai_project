# app/modules/places/schemas.py

from typing import Dict, List, Optional

from pydantic import BaseModel


class PlaceListItem(BaseModel):
    content_id: str
    category: str
    title: str
    addr1: Optional[str] = None
    image_url: Optional[str] = None
    tags: List[str] = []
    distance_km: Optional[float] = None  # lat/lng을 넘겼을 때만 채워짐

    class Config:
        from_attributes = True


class PlaceListResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[PlaceListItem]


class PlaceDetail(BaseModel):
    content_id: str
    category: str
    title: str
    addr1: Optional[str] = None
    addr2: Optional[str] = None
    tel: Optional[str] = None
    mapx: Optional[float] = None
    mapy: Optional[float] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    region: Optional[str] = None
    tags: List[str] = []

    class Config:
        from_attributes = True


class PlaceSeedResponse(BaseModel):
    message: str
    counts: Dict[str, int]  # 카테고리 슬러그 -> 적재 건수
