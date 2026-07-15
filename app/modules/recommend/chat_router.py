# app/modules/recommend/chat_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.recommend.chat_schemas import ChatRequest, ChatResponse
from app.modules.recommend.chat_service import get_chat_response
from app.modules.recommend import crud as weather_crud
from app.modules.recommend.service import DEFAULT_NX, DEFAULT_NY

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


@router.get("/weather/current", tags=["chat"])
def get_current_weather(db: Session = Depends(get_db)):
    """프론트 날씨 위젯용 — 저장된 예보 중 현재와 가장 가까운 것 하나 반환."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now_kst = datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)
    weather = weather_crud.get_nearest_weather(db, target_at=now_kst)

    if weather is None:
        raise HTTPException(status_code=404, detail="저장된 날씨 예보가 없습니다.")

    return {
        "forecast_at": weather.forecast_at,
        "temperature": weather.temperature,
        "rain_prob": weather.rain_prob,
        "rain_type": weather.rain_type,
        "sky_type": weather.sky_type,
    }