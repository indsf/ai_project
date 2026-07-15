# app/modules/places/crud.py

from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.weather_tags import encode_tags, infer_tags
from app.modules.places.models import Place


def _to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def upsert_place(db: Session, item: dict, region: str, content_type_id: str) -> Place:
    """
    TourAPI 원본 item 하나를 places 테이블에 upsert 한다.
    content_id가 이미 있으면 최신 값으로 갱신하고, 없으면 새로 만든다.
    날씨 적합도 태그는 제목 기반 휴리스틱(app.core.weather_tags)으로 자동 추론해서 같이 저장한다.
    """

    content_id = str(item.get("contentid", "")).strip()
    title = item.get("title") or ""

    place = db.query(Place).filter(Place.content_id == content_id).first()

    fields = dict(
        content_type_id=str(content_type_id),
        title=title,
        addr1=item.get("addr1") or None,
        addr2=item.get("addr2") or None,
        tel=item.get("tel") or None,
        mapx=_to_float(item.get("mapx")),
        mapy=_to_float(item.get("mapy")),
        image_url=item.get("firstimage") or None,
        thumbnail_url=item.get("firstimage2") or None,
        region=region,
        tags_raw=encode_tags(infer_tags(title, content_type_id)),
        source_created_time=item.get("createdtime") or None,
        source_modified_time=item.get("modifiedtime") or None,
    )

    if place is None:
        place = Place(content_id=content_id, **fields)
        db.add(place)
    else:
        for key, value in fields.items():
            setattr(place, key, value)

    return place


def bulk_upsert_places(
    db: Session, items: list[dict], region: str, content_type_id: str
) -> int:
    count = 0
    for item in items:
        if not item.get("contentid"):
            continue
        upsert_place(db, item, region, content_type_id)
        count += 1

    db.commit()
    return count


def query_places(
    db: Session,
    search: Optional[str] = None,
    tags: Optional[list[str]] = None,
    match: str = "any",
    content_type_ids: Optional[list[str]] = None,
):
    """
    검색/태그/카테고리 조건으로 필터링된 쿼리(정렬·페이지네이션 전)를 반환한다.
    lat/lng 거리순 정렬이 필요한 호출부(service.py)에서 이 쿼리로 전체를 가져와
    파이썬에서 거리 계산 후 정렬한다.
    """

    query = db.query(Place)

    if content_type_ids:
        query = query.filter(Place.content_type_id.in_(content_type_ids))

    if search:
        query = query.filter(
            or_(
                Place.title.contains(search),
                Place.addr1.contains(search),
            )
        )

    if tags:
        conditions = [Place.tags_raw.contains(f",{tag},") for tag in tags]
        if match == "all":
            for condition in conditions:
                query = query.filter(condition)
        else:
            query = query.filter(or_(*conditions))

    return query


def list_places(
    db: Session,
    search: Optional[str],
    page: int,
    size: int,
    tags: Optional[list[str]] = None,
    match: str = "any",
    content_type_ids: Optional[list[str]] = None,
):
    """거리순 정렬이 필요 없는 일반 목록 조회 (DB 레벨 페이지네이션)."""

    query = query_places(
        db, search=search, tags=tags, match=match, content_type_ids=content_type_ids
    )

    total = query.count()

    items = (
        query.order_by(Place.title.asc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return total, items


def get_place(db: Session, content_id: str) -> Optional[Place]:
    return db.query(Place).filter(Place.content_id == content_id).first()
