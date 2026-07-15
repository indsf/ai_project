# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, SessionLocal, engine
from app.core.weather_tags import tag_docs_table
# 커뮤니티 게시판
from app.modules.posts import models as posts_models  # noqa: F401
from app.modules.posts.router import router as posts_router
# 장소 정보 (TourAPI, 8개 카테고리 통합)
from app.modules.places import models as places_models  # noqa: F401
from app.modules.places.categories import category_docs_table
from app.modules.places.router import router as places_router
from app.modules.places.service import seed_all as seed_places
# 날씨 (기상청 단기예보)
from app.modules.recommend import models as recommend_models  # noqa: F401
from app.modules.recommend.router import router as recommend_router
from app.modules.recommend.service import process_and_save_weather, DEFAULT_NX, DEFAULT_NY
# 챗봇
from app.modules.recommend.chat_router import router as chat_router
API_DESCRIPTION = f"""
구미·경북권 지역정보 커뮤니티 **LocalHub** 백엔드 API.
- 로그인/인증 없음 (비밀번호는 게시글 단위로만 씀)
- 모든 응답은 JSON
- 원본 관광 데이터 출처: 한국관광공사 Tour API(TourAPI 4.0), 공공누리 제3유형(출처표시+변경금지)
## 모듈 구성
| 모듈 | 설명 |
|---|---|
| **커뮤니티** (`/api/posts`) | 유저가 직접 쓰는 게시글 |
| **장소** (`/api/places`) | TourAPI 원본 데이터 8개 카테고리 통합 검색 |
| **날씨** (`/api/recommend/weather`) | 기상청 단기예보 |
| **챗봇** (`/api/chat`) | 게시글+장소+날씨 기반 안내 챗봇 |
## 장소 카테고리 (`category` 파라미터에 쓰는 값)
{category_docs_table()}
## 날씨 적합도 태그 (`tags` 파라미터에 쓰는 값)
{tag_docs_table()}
""".strip()
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="LocalHub API",
    description=API_DESCRIPTION,
    version="0.2.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(posts_router)
app.include_router(places_router)
app.include_router(recommend_router)
app.include_router(chat_router)
@app.on_event("startup")
def _seed_places_data() -> None:
    db = SessionLocal()
    try:
        seed_places(db)
    finally:
        db.close()
@app.on_event("startup")
async def _fetch_initial_weather() -> None:
    """서버 기동 시 기상청 날씨를 한 번 받아와 DB에 저장한다."""
    db = SessionLocal()
    try:
        await process_and_save_weather(db, nx=DEFAULT_NX, ny=DEFAULT_NY)
        print("[startup] 날씨 데이터 초기 적재 완료")
    except Exception as e:
        print(f"[startup] 날씨 초기 적재 실패 (앱은 계속 실행됨): {e}")
    finally:
        db.close()
@app.get("/api", tags=["health"], summary="헬스체크")
def health_check():
    return {"status": "ok", "message": "LocalHub API is running"}