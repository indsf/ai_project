# app/modules/places/schemas.py

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PlaceListItem(BaseModel):
    content_id: str = Field(..., description="TourAPI 원본 고유 ID", examples=["3028462"])
    category: str = Field(
        ..., description="카테고리 슬러그 (전체 목록은 최상단 API 설명 참고)", examples=["festivals"]
    )
    title: str = Field(..., examples=["구미라면 축제"])
    addr1: Optional[str] = Field(None, examples=["경상북도 구미시 원평동"])
    image_url: Optional[str] = Field(
        None, examples=["https://tong.visitkorea.or.kr/cms/resource/40/3497640_image2_1.jpg"]
    )
    tags: List[str] = Field(default_factory=list, examples=[["outdoor", "sunny"]])
    distance_km: Optional[float] = Field(
        None, description="lat/lng을 넘겼을 때만 채워짐 (안 넘기면 null)", examples=[1.24]
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "content_id": "3028462",
                "category": "festivals",
                "title": "구미라면 축제",
                "addr1": "경상북도 구미시 원평동",
                "image_url": "https://tong.visitkorea.or.kr/cms/resource/40/3497640_image2_1.jpg",
                "tags": ["outdoor", "sunny"],
                "distance_km": 1.24,
            }
        }


class PlaceListResponse(BaseModel):
    total: int = Field(..., description="조건에 맞는 전체 건수 (페이지네이션 전)", examples=[30])
    page: int = Field(..., examples=[1])
    size: int = Field(..., examples=[20])
    items: List[PlaceListItem]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 30,
                "page": 1,
                "size": 20,
                "items": [
                    {
                        "content_id": "3028462",
                        "category": "festivals",
                        "title": "구미라면 축제",
                        "addr1": "경상북도 구미시 원평동",
                        "image_url": "https://tong.visitkorea.or.kr/cms/resource/40/3497640_image2_1.jpg",
                        "tags": ["outdoor", "sunny"],
                        "distance_km": 1.24,
                    }
                ],
            }
        }


class PlaceDetail(BaseModel):
    content_id: str = Field(..., examples=["3028462"])
    category: str = Field(..., examples=["festivals"])
    title: str = Field(..., examples=["구미라면 축제"])
    addr1: Optional[str] = Field(None, examples=["경상북도 구미시 원평동"])
    addr2: Optional[str] = Field(None, examples=["124-23 구미역 일원"])
    tel: Optional[str] = Field(None, examples=["054-480-2652"])
    mapx: Optional[float] = Field(None, description="경도", examples=[128.331422])
    mapy: Optional[float] = Field(None, description="위도", examples=[36.129404])
    image_url: Optional[str] = Field(None)
    thumbnail_url: Optional[str] = Field(None)
    region: Optional[str] = Field(None, examples=["구미_경북권"])
    tags: List[str] = Field(default_factory=list, examples=[["outdoor", "sunny"]])

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "content_id": "3028462",
                "category": "festivals",
                "title": "구미라면 축제",
                "addr1": "경상북도 구미시 원평동",
                "addr2": "124-23 구미역 일원",
                "tel": "054-480-2652",
                "mapx": 128.331422,
                "mapy": 36.129404,
                "image_url": "https://tong.visitkorea.or.kr/cms/resource/40/3497640_image2_1.jpg",
                "thumbnail_url": "https://tong.visitkorea.or.kr/cms/resource/40/3497640_image3_1.jpg",
                "region": "구미_경북권",
                "tags": ["outdoor", "sunny"],
            }
        }


class PlaceSeedResponse(BaseModel):
    message: str = Field(..., examples=["장소 데이터를 적재했습니다."])
    counts: Dict[str, int] = Field(
        ..., description="카테고리 슬러그별 적재 건수", examples=[{"festivals": 30, "restaurants": 394}]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "장소 데이터를 적재했습니다.",
                "counts": {
                    "attractions": 499,
                    "culture": 112,
                    "festivals": 30,
                    "courses": 31,
                    "leisure": 110,
                    "lodging": 80,
                    "shopping": 411,
                    "restaurants": 394,
                },
            }
        }
