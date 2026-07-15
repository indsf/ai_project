# app/modules/festival/service.py
# TourAPI 원본 JSON -> DB 적재 파이프라인 + 다른 모듈에 노출할 공개 인터페이스

import json
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


class FestivalSummary:
    """recommend 모듈 등 외부에 노출하는 요약 DTO. Festival ORM 객체를 그대로 넘기지 않기 위함."""

    def __init__(self, festival: Festival):
        self.content_id = festival.content_id
        self.title = festival.title
        self.addr1 = festival.addr1
        self.mapx = festival.mapx
        self.mapy = festival.mapy
        self.image_url = festival.image_url


def get_festivals_for_recommendation(
    db: Session, search: Optional[str] = None, limit: int = 20
) -> list[FestivalSummary]:
    """recommend 모듈이 호출하는 공개 인터페이스. festival.crud/festival.models 직접 import 금지."""
    _total, items = crud.list_festivals(db, search, page=1, size=limit)
    return [FestivalSummary(f) for f in items]
