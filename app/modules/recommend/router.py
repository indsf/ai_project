# app/modules/recommend/router.py

# front 요청 시 날씨 파이프라인 통신 연결 담당 (HTTP 요청·응답)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.recommend import service

router = APIRouter(
    prefix="/api/recommend",
    tags=["Recommend"] # 나중에 Swagger(API 문서)에서 예쁘게 그룹화해 줍니다.
)

@router.get("/weather")
async def get_weather_recommendation(nx: int = 87, ny: int = 90, db: Session = Depends(get_db)):
    """
    기상청에서 현재 날씨를 가져와 DB에 저장하고, 프론트엔드에 필요한 데이터만 반환합니다.
    """
    # 아까 만든 파이프라인(service) 호출
    saved_weather = await service.process_and_save_weather(db, nx=nx, ny=ny)
    
    # 프론트엔드 개발자가 파싱하기 딱 좋은 깔끔한 JSON 형태로 응답
    return {
        "message": "구미 날씨 조회 및 적재 성공",
        "data": {
            "id": saved_weather.id,
            "temperature": saved_weather.temperature,
            "rain_prob": saved_weather.rain_prob,
            "rain_type": saved_weather.rain_type
        }
    }