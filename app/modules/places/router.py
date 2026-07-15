# app/modules/places/router.py
# 통합 장소 검색 + 카테고리별 조회 HTTP 요청·응답 담당
#
# 라우트 등록 순서 중요: 정적 경로(/seed, /festivals, /restaurants ...)를
# 동적 경로(/{content_id})보다 먼저 등록해야 한다. Starlette은 등록 순서대로 매칭을
# 시도하기 때문에, {content_id}를 먼저 등록하면 "/festivals" 같은 요청도 거기 걸려버린다.

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.places import crud, schemas, service
from app.modules.places.categories import CONTENT_TYPE_REGISTRY, SLUG_TO_CONTENT_TYPE

router = APIRouter(prefix="/api/places", tags=["places"])


def _parse_csv(value: Optional[str]) -> Optional[list[str]]:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _resolve_category_slugs(category: Optional[str]) -> Optional[list[str]]:
    slugs = _parse_csv(category)
    if not slugs:
        return None

    unknown = [s for s in slugs if s not in SLUG_TO_CONTENT_TYPE]
    if unknown:
        valid = ", ".join(sorted(SLUG_TO_CONTENT_TYPE))
        raise HTTPException(
            status_code=400,
            detail=f"알 수 없는 category: {unknown}. 가능한 값: {valid}",
        )

    return [SLUG_TO_CONTENT_TYPE[s] for s in slugs]


# ── 1. 통합 검색 ──────────────────────────────────────────────────────────
@router.get("", response_model=schemas.PlaceListResponse)
def search_places(
    search: Optional[str] = None,
    category: Optional[str] = Query(
        None, description="쉼표로 구분된 카테고리 슬러그. 예: festivals,restaurants (안 넘기면 전체)"
    ),
    tags: Optional[str] = Query(
        None, description="쉼표로 구분된 태그 목록. 예: rain,indoor"
    ),
    match: str = Query(
        "any", pattern="^(any|all)$", description="'any'면 태그 중 하나만 맞아도, 'all'이면 전부 맞아야 함"
    ),
    lat: Optional[float] = Query(None, description="현재 위치 위도 (선택)"),
    lng: Optional[float] = Query(None, description="현재 위치 경도 (선택)"),
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    """
    출처: 한국관광공사 Tour API(TourAPI 4.0)
    (https://www.data.go.kr/data/15101578/openapi.do), 공공누리 제3유형

    카테고리를 안 넘기면 8개 카테고리를 전부 합쳐서 검색한다.
    특정 카테고리만 보고 싶으면 category=festivals 처럼 넘기거나,
    아래의 카테고리 전용 엔드포인트(/api/places/festivals 등)를 쓰면 된다.
    """

    content_type_ids = _resolve_category_slugs(category)
    tag_list = _parse_csv(tags)

    total, items = service.list_places_with_distance(
        db,
        search=search,
        page=page,
        size=size,
        tags=tag_list,
        match=match,
        lat=lat,
        lng=lng,
        content_type_ids=content_type_ids,
    )
    return schemas.PlaceListResponse(total=total, page=page, size=size, items=items)


# ── 2. 전체 카테고리 시딩 ────────────────────────────────────────────────
@router.post("/seed", response_model=schemas.PlaceSeedResponse, status_code=201)
def seed_places(db: Session = Depends(get_db)):
    """
    app/data 안의 TourAPI 원본 JSON(8개 카테고리)을 읽어 places 테이블에 적재(upsert)한다.
    파일이 없는 카테고리는 0건으로 건너뛴다. 여러 번 호출해도 안전하다.
    태그도 이 과정에서 자동으로 (재)계산된다.
    """
    counts = service.seed_all(db)
    return schemas.PlaceSeedResponse(message="장소 데이터를 적재했습니다.", counts=counts)


# ── 3. 카테고리 전용 엔드포인트 (통합검색과 로직은 동일, 카테고리만 고정) ──
def _make_category_endpoint(content_type_id: str):
    def endpoint(
        search: Optional[str] = None,
        tags: Optional[str] = Query(None, description="쉼표로 구분된 태그 목록. 예: rain,indoor"),
        match: str = Query("any", pattern="^(any|all)$"),
        lat: Optional[float] = None,
        lng: Optional[float] = None,
        page: int = 1,
        size: int = 20,
        db: Session = Depends(get_db),
    ):
        tag_list = _parse_csv(tags)
        total, items = service.list_places_with_distance(
            db,
            search=search,
            page=page,
            size=size,
            tags=tag_list,
            match=match,
            lat=lat,
            lng=lng,
            content_type_ids=[content_type_id],
        )
        return schemas.PlaceListResponse(total=total, page=page, size=size, items=items)

    return endpoint


for _content_type_id, _meta in CONTENT_TYPE_REGISTRY.items():
    router.add_api_route(
        f"/{_meta['slug']}",
        _make_category_endpoint(_content_type_id),
        methods=["GET"],
        response_model=schemas.PlaceListResponse,
        name=f"list_places_{_meta['slug']}",
        summary=f"{_meta['label']} 목록 (카테고리 고정)",
        tags=["places"],
    )


# ── 4. 단건 상세 (반드시 마지막에 등록 — 위의 정적 경로들과 겹치지 않게) ──
@router.get("/{content_id}", response_model=schemas.PlaceDetail)
def get_place_detail(content_id: str, db: Session = Depends(get_db)):
    place = crud.get_place(db, content_id)
    if not place:
        raise HTTPException(status_code=404, detail="장소 정보를 찾을 수 없습니다.")
    return place
