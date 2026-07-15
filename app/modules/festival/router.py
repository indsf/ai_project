# app/modules/festival/router.py
# 축제 정보(한국관광공사 TourAPI 원본) HTTP 요청·응답 담당

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.festival import crud, schemas, service

router = APIRouter(prefix="/api/festivals", tags=["festival"])


@router.get("", response_model=schemas.FestivalListResponse)
def get_festivals(
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
):
    """
    출처: 한국관광공사 Tour API(TourAPI 4.0)
    (https://www.data.go.kr/data/15101578/openapi.do), 공공누리 제3유형
    """
    total, items = crud.list_festivals(db, search, page, size)
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
    """
    try:
        count = service.seed_festivals(db)
    except FileNotFoundError as error:
        raise HTTPException(status_code=500, detail=str(error))

    return schemas.FestivalSeedResponse(
        message="축제 데이터를 적재했습니다.", count=count
    )
