# app/modules/festival/crud.py

from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.modules.festival.models import Festival


def _to_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def upsert_festival(db: Session, item: dict, region: str) -> Festival:
    """
    TourAPI 원본 item 하나를 festivals 테이블에 upsert 한다.
    content_id가 이미 있으면 최신 값으로 갱신하고, 없으면 새로 만든다.
    """

    content_id = str(item.get("contentid", "")).strip()

    festival = (
        db.query(Festival).filter(Festival.content_id == content_id).first()
    )

    fields = dict(
        title=item.get("title") or "",
        addr1=item.get("addr1") or None,
        addr2=item.get("addr2") or None,
        tel=item.get("tel") or None,
        mapx=_to_float(item.get("mapx")),
        mapy=_to_float(item.get("mapy")),
        image_url=item.get("firstimage") or None,
        thumbnail_url=item.get("firstimage2") or None,
        region=region,
        source_created_time=item.get("createdtime") or None,
        source_modified_time=item.get("modifiedtime") or None,
    )

    if festival is None:
        festival = Festival(content_id=content_id, **fields)
        db.add(festival)
    else:
        for key, value in fields.items():
            setattr(festival, key, value)

    return festival


def bulk_upsert_festivals(db: Session, items: list[dict], region: str) -> int:
    count = 0
    for item in items:
        if not item.get("contentid"):
            continue
        upsert_festival(db, item, region)
        count += 1

    db.commit()
    return count


def list_festivals(db: Session, search: Optional[str], page: int, size: int):
    query = db.query(Festival)

    if search:
        query = query.filter(
            or_(
                Festival.title.contains(search),
                Festival.addr1.contains(search),
            )
        )

    total = query.count()

    items = (
        query.order_by(Festival.title.asc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )

    return total, items


def get_festival(db: Session, content_id: str) -> Optional[Festival]:
    return db.query(Festival).filter(Festival.content_id == content_id).first()


def count_festivals(db: Session) -> int:
    return db.query(Festival).count()