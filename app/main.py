# app/main.py
from fastapi import FastAPI
from app.core.database import engine, Base

# 앱 모듈 임포트
from app.modules.recommend import models as recommend_models
from app.modules.recommend.router import router as recommend_router

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 서버 애플리케이션 객체 생성
app = FastAPI(title="해커톤 날씨 추천 API")

# 💡 여기에 아까 만든 라우터(창구)를 꽂아줍니다!
app.include_router(recommend_router)