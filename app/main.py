# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, SessionLocal, engine

# 커뮤니티 게시판
from app.modules.posts import models as posts_models  # noqa: F401  (Base.metadata에 테이블 등록용)
from app.modules.posts.router import router as posts_router

# 축제 정보 (TourAPI)
from app.modules.festival import models as festival_models  # noqa: F401
from app.modules.festival.router import router as festival_router
from app.modules.festival.service import seed_festivals

# ── weater_feature 브랜치 병합 후 아래 두 줄의 주석을 해제하세요 ──────────────
# from app.modules.recommend import models as recommend_models
# from app.modules.recommend.router import router as recommend_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LocalHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts_router)
app.include_router(festival_router)
# app.include_router(recommend_router)


@app.on_event("startup")
def _seed_festival_data() -> None:
    """서버 기동 시 TourAPI 축제 데이터를 자동으로 적재한다(upsert라 반복 실행해도 안전)."""
    db = SessionLocal()
    try:
        seed_festivals(db)
    finally:
        db.close()


@app.get("/api")
def health_check():
    return {"status": "ok", "message": "LocalHub API is running"}
