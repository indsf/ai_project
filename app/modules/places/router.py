# app/modules/places/router.py
# 통합 장소 검색 + 카테고리별 조회 HTTP 요청·응답 담당
#
# 라우트 등록 순서 중요: 정적 경로(/seed, /festivals, /restaurants ...)를
# 동적 경로(/{content_id})보다 먼저 등록해야 한다. Starlette은 등록 순서대로 매칭을
# 시도하기 때문에, {content_id}를 먼저 등록하면 "/festivals" 같은 요청도 거기 걸려버린다.

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.weather_tags import tag_docs_table, tag_vocabulary_csv
from app.modules.places import crud, schemas, service
from app.modules.places.categories import (
    CONTENT_TYPE_REGISTRY,
    SLUG_TO_CONTENT_TYPE,
    category_docs_table,
    category_slugs_csv,
)

router = APIRouter(prefix="/api/places", tags=["places"])

_TAGS_QUERY_DESC = f"쉼표로 구분된 태그 목록. 예: rain,indoor. 가능한 값: {tag_vocabulary_csv()}"
_MATCH_QUERY_DESC = "'any'(기본값)면 태그 중 하나만 맞아도, 'all'이면 태그를 전부 가진 경우만 포함"


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
        valid = category_slugs_csv()
        raise HTTPException(
            status_code=400,
            detail=f"알 수 없는 category: {unknown}. 가능한 값: {valid}",
        )

    return [SLUG_TO_CONTENT_TYPE[s] for s in slugs]


# ── 1. 통합 검색 ──────────────────────────────────────────────────────────
@router.get(
    "",
    response_model=schemas.PlaceListResponse,
    summary="장소 통합 검색",
    description=f"""
8개 카테고리(관광지/레포츠/문화시설/쇼핑/숙박/여행코스/음식점/축제공연행사)를 한 번에 검색한다.
`category`를 안 넘기면 전부 합쳐서 검색하고, 넘기면 그 카테고리만 필터링한다.

**카테고리 값**

{category_docs_table()}

**태그 값**

{tag_docs_table()}

출처: 한국관광공사 Tour API(TourAPI 4.0), 공공누리 제3유형(출처표시+변경금지)
""".strip(),
)
def search_places(
    search: Optional[str] = Query(None, description="제목/주소에 대한 부분 검색어", examples=["구미"]),
    category: Optional[str] = Query(
        None,
        description=f"쉼표로 구분된 카테고리 슬러그. 안 넘기면 전체. 가능한 값: {category_slugs_csv()}",
        examples=["festivals,restaurants"],
    ),
    tags: Optional[str] = Query(None, description=_TAGS_QUERY_DESC, examples=["rain,indoor"]),
    match: str = Query("any", pattern="^(any|all)$", description=_MATCH_QUERY_DESC, examples=["any"]),
    lat: Optional[float] = Query(None, description="현재 위치 위도 (선택, lng과 같이 넘겨야 함)", examples=[36.129404]),
    lng: Optional[float] = Query(None, description="현재 위치 경도 (선택, lat과 같이 넘겨야 함)", examples=[128.331422]),
    page: int = Query(1, ge=1, examples=[1]),
    size: int = Query(20, ge=1, le=100, examples=[20]),
    db: Session = Depends(get_db),
):
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
@router.post(
    "/seed",
    response_model=schemas.PlaceSeedResponse,
    status_code=201,
    summary="전체 카테고리 재시딩",
    description=(
        "app/data 안의 TourAPI 원본 JSON(8개 카테고리)을 읽어 places 테이블에 적재(upsert)한다. "
        "파일이 없는 카테고리는 0건으로 건너뛴다. 여러 번 호출해도 안전하다(idempotent). "
        "태그도 이 과정에서 자동으로 (재)계산된다. 서버 기동 시 자동으로도 실행되므로 보통은 직접 "
        "호출할 필요 없다."
    ),
)
def seed_places(db: Session = Depends(get_db)):
    counts = service.seed_all(db)
    return schemas.PlaceSeedResponse(message="장소 데이터를 적재했습니다.", counts=counts)


# ── 3. 카테고리 전용 엔드포인트 (통합검색과 로직은 동일, 카테고리만 고정) ──
def _make_category_endpoint(content_type_id: str, label: str):
    def endpoint(
        search: Optional[str] = Query(None, description="제목/주소에 대한 부분 검색어"),
        tags: Optional[str] = Query(None, description=_TAGS_QUERY_DESC, examples=["rain,indoor"]),
        match: str = Query("any", pattern="^(any|all)$", description=_MATCH_QUERY_DESC),
        lat: Optional[float] = Query(None, description="현재 위치 위도 (선택)"),
        lng: Optional[float] = Query(None, description="현재 위치 경도 (선택)"),
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
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
        _make_category_endpoint(_content_type_id, _meta["label"]),
        methods=["GET"],
        response_model=schemas.PlaceListResponse,
        name=f"list_places_{_meta['slug']}",
        summary=f"{_meta['label']} 목록",
        description=(
            f"카테고리가 `{_meta['slug']}`({_meta['label']})로 고정된 목록 조회. "
            f"검색/태그필터/거리순 정렬 파라미터는 통합검색(`GET /api/places`)과 동일하다."
        ),
        tags=["places"],
    )


# ── 4. 단건 상세 (반드시 마지막에 등록 — 위의 정적 경로들과 겹치지 않게) ──
@router.get(
    "/{content_id}",
    response_model=schemas.PlaceDetail,
    summary="장소 상세 조회",
    description="카테고리 상관없이 content_id 하나로 상세 정보를 조회한다.",
)
def get_place_detail(
    content_id: str = Path(..., description="TourAPI 원본 고유 ID", examples=["3028462"]),
    db: Session = Depends(get_db),
):
    place = crud.get_place(db, content_id)
    if not place:
        raise HTTPException(status_code=404, detail="장소 정보를 찾을 수 없습니다.")
    return place
