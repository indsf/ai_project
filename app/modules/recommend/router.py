from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.recommend.schemas import ChatRequest, ChatResponse
from app.modules.recommend.chat_service import get_chat_response

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
