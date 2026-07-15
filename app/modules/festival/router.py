# app/modules/festival/router.py
# 축제 정보(한국관광공사 TourAPI 원본) HTTP 요청·응답 담당

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.festival import crud, schemas, service

router = APIRouter(prefix="/api/festivals", tags=["festival"])


@router.get("", response_model=schemas.FestivalListResponse)
def get_festivals(
    search: Optional[str] = None,
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

    - tags 없이 호출: 전체 축제 목록 (제목순)
    - tags=rain,indoor : 태그가 rain 또는 indoor(match=any, 기본값)인 축제만
    - tags=rain,indoor&match=all : 두 태그를 모두 가진 축제만
    - lat/lng을 같이 넘기면 각 항목에 distance_km이 채워지고 가까운 순으로 정렬됨.
      lat/lng을 넘기지 않으면 distance_km은 null이고 제목순 정렬.
    """

    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    total, items = service.list_festivals_with_distance(
        db,
        search=search,
        page=page,
        size=size,
        tags=tag_list,
        match=match,
        lat=lat,
        lng=lng,
    )
    return schemas.FestivalListResponse(total=total, page=page, size=size, items=items)


@router.get("/{content_id}", response_model=schemas.FestivalDetail)
def get_festival_detail(content_id: str, db: Session = Depends(get_db)):
    festival = crud.get_festival(db, content_id)
    if not festival:
        raise HTTPException(status_code=404, detail="축제 정보를 찾을 수 없습니다.")
    return festival


@router.post("/seed", response_model=schemas.FestivalSeedResponse, status_code=201)
def seed_festivals(db: Session = Depends(get_db)):
    """
    app/data 안의 TourAPI 원본 JSON을 읽어 festivals 테이블에 적재(upsert)한다.
    이미 적재된 데이터가 있어도 다시 호출하면 최신 값으로 갱신될 뿐 중복 생성되지 않는다.
    태그도 이 과정에서 자동으로 (재)계산된다.
    """
    try:
        count = service.seed_festivals(db)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))

    return schemas.FestivalSeedResponse(
        message="축제 데이터를 적재했습니다.", count=count
    )
