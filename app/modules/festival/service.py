# app/modules/festival/service.py
# TourAPI 원본 JSON -> DB 적재 파이프라인 + 다른 모듈에 노출할 공개 인터페이스

import json
import math
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import FESTIVAL_DATA_PATH
from app.modules.festival import crud
from app.modules.festival.models import Festival


def seed_festivals(db: Session, path: Optional[Path] = None) -> int:
    """
    app/data/*.json (한국관광공사 TourAPI 축제공연행사 원본)을 읽어
    festivals 테이블에 upsert 한다. 이미 있는 데이터는 값을 갱신하고,
    새 데이터는 추가하므로 여러 번 실행해도 안전하다(idempotent).
    날씨 적합도 태그(tags)는 이 과정에서 제목 기반으로 자동 추론되어 함께 저장된다.
    """

    target_path = path or FESTIVAL_DATA_PATH

    if not target_path.exists():
        raise FileNotFoundError(
            f"축제 데이터 파일을 찾을 수 없습니다: {target_path}"
        )

    with open(target_path, encoding="utf-8") as f:
        payload = json.load(f)

    region = payload.get("region", "")
    items = payload.get("items", [])

    return crud.bulk_upsert_festivals(db, items, region)


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


def list_festivals_with_distance(
    db: Session,
    search: Optional[str],
    page: int,
    size: int,
    tags: Optional[list[str]] = None,
    match: str = "any",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
):
    """
    search/tags로 필터링한 축제 목록을 반환한다.
    lat/lng이 함께 오면 각 항목에 distance_km을 채우고 가까운 순으로 정렬해서
    파이썬 레벨에서 페이지네이션한다. lat/lng이 없으면 기존처럼 제목순 + DB 페이지네이션.
    """

    if lat is None or lng is None:
        return crud.list_festivals(db, search, page, size, tags=tags, match=match)

    query = crud.query_festivals(db, search=search, tags=tags, match=match)
    all_items: list[Festival] = query.all()

    with_coords = [f for f in all_items if f.mapx is not None and f.mapy is not None]
    without_coords = [f for f in all_items if f not in with_coords]

    for festival in with_coords:
        festival.distance_km = round(
            _haversine_km(lat, lng, festival.mapy, festival.mapx), 2
        )

    with_coords.sort(key=lambda f: f.distance_km)

    for festival in without_coords:
        festival.distance_km = None

    ordered = with_coords + without_coords
    total = len(ordered)

    start = (page - 1) * size
    page_items = ordered[start : start + size]

    return total, page_items


class FestivalSummary:
    """recommend 모듈 등 외부에 노출하는 요약 DTO. Festival ORM 객체를 그대로 넘기지 않기 위함."""

    def __init__(self, festival: Festival):
        self.content_id = festival.content_id
        self.title = festival.title
        self.addr1 = festival.addr1
        self.mapx = festival.mapx
        self.mapy = festival.mapy
        self.image_url = festival.image_url
        self.tags = festival.tags


def get_festivals_for_recommendation(
    db: Session,
    search: Optional[str] = None,
    tags: Optional[list[str]] = None,
    match: str = "any",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    limit: int = 20,
) -> list[FestivalSummary]:
    """
    recommend 모듈이 호출하는 공개 인터페이스. festival.crud/festival.models 직접 import 금지.
    예: get_festivals_for_recommendation(db, tags=["rain", "indoor"], lat=36.13, lng=128.33)
    """
    _total, items = list_festivals_with_distance(
        db, search=search, page=1, size=limit, tags=tags, match=match, lat=lat, lng=lng
    )
    return [FestivalSummary(f) for f in items]
