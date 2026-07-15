# app/modules/places/service.py
# TourAPI 원본 JSON(8개 카테고리) -> DB 적재 파이프라인 + 다른 모듈에 노출할 공개 인터페이스

import json
import math
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import PLACES_DATA_DIR
from app.modules.places import crud
from app.modules.places.categories import CONTENT_TYPE_REGISTRY, SLUG_TO_CONTENT_TYPE
from app.modules.places.models import Place


def seed_category(
    db: Session, content_type_id: str, path: Optional[Path] = None
) -> int:
    """카테고리 하나(예: 축제)의 원본 JSON을 읽어 upsert 한다. 여러 번 실행해도 안전하다."""

    meta = CONTENT_TYPE_REGISTRY.get(content_type_id)
    if meta is None:
        raise ValueError(f"알 수 없는 content_type_id: {content_type_id}")

    target_path = path or (PLACES_DATA_DIR / meta["file"])

    if not target_path.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {target_path}")

    with open(target_path, encoding="utf-8") as f:
        payload = json.load(f)

    region = payload.get("region", "")
    items = payload.get("items", [])

    return crud.bulk_upsert_places(db, items, region, content_type_id)


def seed_all(db: Session) -> dict[str, int]:
    """
    8개 카테고리를 전부 시딩한다. 데이터 파일이 아직 없는 카테고리는 0건으로 건너뛴다
    (다른 모듈 담당자가 나중에 파일만 app/data에 넣으면 바로 채워짐).
    """

    results: dict[str, int] = {}
    for content_type_id, meta in CONTENT_TYPE_REGISTRY.items():
        try:
            results[meta["slug"]] = seed_category(db, content_type_id)
        except FileNotFoundError:
            results[meta["slug"]] = 0

    return results


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 사이의 거리(km)를 계산한다."""

    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def list_places_with_distance(
    db: Session,
    search: Optional[str],
    page: int,
    size: int,
    tags: Optional[list[str]] = None,
    match: str = "any",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    content_type_ids: Optional[list[str]] = None,
):
    """
    search/tags/category로 필터링한 장소 목록을 반환한다.
    lat/lng이 함께 오면 각 항목에 distance_km을 채우고 가까운 순으로 정렬해서
    파이썬 레벨에서 페이지네이션한다. lat/lng이 없으면 제목순 + DB 페이지네이션.
    """

    if lat is None or lng is None:
        return crud.list_places(
            db, search, page, size, tags=tags, match=match, content_type_ids=content_type_ids
        )

    query = crud.query_places(
        db, search=search, tags=tags, match=match, content_type_ids=content_type_ids
    )
    all_items: list[Place] = query.all()

    with_coords = [p for p in all_items if p.mapx is not None and p.mapy is not None]
    without_coords = [p for p in all_items if p not in with_coords]

    for place in with_coords:
        place.distance_km = round(_haversine_km(lat, lng, place.mapy, place.mapx), 2)

    with_coords.sort(key=lambda p: p.distance_km)

    for place in without_coords:
        place.distance_km = None

    ordered = with_coords + without_coords
    total = len(ordered)

    start = (page - 1) * size
    page_items = ordered[start : start + size]

    return total, page_items


class PlaceSummary:
    """recommend 모듈 등 외부에 노출하는 요약 DTO. Place ORM 객체를 그대로 넘기지 않기 위함."""

    def __init__(self, place: Place):
        self.content_id = place.content_id
        self.category = place.category
        self.title = place.title
        self.addr1 = place.addr1
        self.mapx = place.mapx
        self.mapy = place.mapy
        self.image_url = place.image_url
        self.tags = place.tags


def get_places_for_recommendation(
    db: Session,
    categories: Optional[list[str]] = None,  # 슬러그: ["festivals","restaurants"]
    tags: Optional[list[str]] = None,
    match: str = "any",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    limit: int = 20,
) -> list[PlaceSummary]:
    """
    recommend 모듈이 호출하는 공개 인터페이스. places.crud/places.models 직접 import 금지.
    예: get_places_for_recommendation(db, categories=["festivals"], tags=["rain"], lat=36.13, lng=128.33)
    """

    content_type_ids = None
    if categories:
        content_type_ids = [SLUG_TO_CONTENT_TYPE[c] for c in categories if c in SLUG_TO_CONTENT_TYPE]

    _total, items = list_places_with_distance(
        db,
        search=None,
        page=1,
        size=limit,
        tags=tags,
        match=match,
        lat=lat,
        lng=lng,
        content_type_ids=content_type_ids,
    )
    return [PlaceSummary(p) for p in items]
