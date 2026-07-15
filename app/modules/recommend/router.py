# app/modules/recommend/router.py
# front 요청 시 날씨 파이프라인 통신 연결 담당 (HTTP 요청·응답)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.recommend import service
from app.modules.recommend.festivals import get_festival_recommendations

router = APIRouter(
    prefix="/api/recommend",
    tags=["Recommend"],
)


@router.get("/weather", summary="구미 날씨 조회 및 저장")
async def get_weather_recommendation(
    nx: int = Query(default=84, description="기상청 격자 X 좌표"),
    ny: int = Query(default=96, description="기상청 격자 Y 좌표"),
    db: Session = Depends(get_db),
):
    """기상청 단기예보를 조회하여 DB에 저장한 뒤, 현재 시각에 가장 가까운 예보와 추천 태그를 반환한다."""
    try:
        saved_forecasts = await service.process_and_save_weather(db=db, nx=nx, ny=ny)
        weather_context = service.get_current_weather_context(db)

        return {
            "message": "구미 날씨 조회 및 적재 성공",
            "saved_count": len(saved_forecasts),
            "data": {
                "weather_id": weather_context["weather_id"],
                "forecast_at": weather_context["forecast_at"],
                "temperature": weather_context["temperature"],
                "rain_prob": weather_context["rain_prob"],
                "rain_type": weather_context["rain_type"],
                "sky_type": weather_context["sky_type"],
                "normalized_weather": weather_context["normalized_weather"],
                "place_tags": weather_context["place_tags"],
            },
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/festivals", summary="현재 날씨 기반 축제 추천")
def get_recommended_festivals(
    lat: float | None = Query(default=None, description="사용자의 현재 위치 위도"),
    lng: float | None = Query(default=None, description="사용자의 현재 위치 경도"),
    limit: int = Query(default=10, ge=1, le=30, description="반환할 추천 축제 개수"),
    db: Session = Depends(get_db),
):
    """DB에 저장된 현재 예보를 기준으로 날씨를 정규화하고, 날씨 태그와 축제 태그를 비교해 추천 점수를 계산한다."""
    try:
        return get_festival_recommendations(db=db, lat=lat, lng=lng, limit=limit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error