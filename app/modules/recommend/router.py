from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.recommend.schemas import ChatRequest, ChatResponse, WeatherForecastResponse
from app.modules.recommend.chat_service import get_chat_response
from app.modules.recommend import weather_crud, weather_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="메시지를 입력해주세요.")
    try:
        reply, related_ids = get_chat_response(request.message, request.history, db)
    except Exception as e:
        print("Chat error:", e)
        raise HTTPException(status_code=500, detail="챗봇 응답 생성에 실패했습니다. 잠시 후 다시 시도해주세요.")
    return ChatResponse(reply=reply, related_post_ids=related_ids)


@router.post("/weather/refresh", response_model=list[WeatherForecastResponse])
async def refresh_weather(db: Session = Depends(get_db)):
    """기상청 API를 호출해 최신 날씨를 DB에 저장하고 반환한다."""
    try:
        forecasts = await weather_service.process_and_save_weather(db=db)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return forecasts


@router.get("/weather", response_model=list[WeatherForecastResponse])
def get_weather(db: Session = Depends(get_db)):
    """DB에 저장된 최신 날씨 예보를 조회한다."""
    forecasts = weather_crud.get_forecasts(
        db=db,
        nx=weather_service.DEFAULT_NX,
        ny=weather_service.DEFAULT_NY,
    )
    return forecasts