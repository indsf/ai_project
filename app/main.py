# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.core.database import Base, SessionLocal, engine
from app.core.weather_tags import tag_docs_table

# 커뮤니티 게시판
from app.modules.posts import models as posts_models  # noqa: F401  (Base.metadata에 테이블 등록용)
from app.modules.posts.router import router as posts_router

# 장소 정보 (TourAPI, 8개 카테고리 통합)
from app.modules.places import models as places_models  # noqa: F401
from app.modules.places.categories import category_docs_table
from app.modules.places.router import router as places_router
from app.modules.places.service import seed_all as seed_places

# ── weater_feature 브랜치 병합 후 아래 두 줄의 주석을 해제하세요 ──────────────
from app.modules.recommend import models as recommend_models
from app.modules.recommend.router import router as recommend_router


API_DESCRIPTION = f"""
구미·경북권 지역정보 커뮤니티 **LocalHub** 백엔드 API.

- 로그인/인증 없음 (비밀번호는 게시글 단위로만 씀)
- 모든 응답은 JSON
- 원본 관광 데이터 출처: 한국관광공사 Tour API(TourAPI 4.0), 공공누리 제3유형(출처표시+변경금지)

## 모듈 구성

| 모듈 | 설명 |
|---|---|
| **커뮤니티** (`/api/posts`) | 유저가 직접 쓰는 게시글 (축제 후기/관광지 추천/맛집 등) |
| **장소** (`/api/places`) | TourAPI 원본 데이터 8개 카테고리 통합 검색 |

## 장소 카테고리 (`category` 파라미터에 쓰는 값)

{category_docs_table()}

`category=festivals,restaurants` 처럼 쉼표로 여러 개 같이 넘길 수 있고,
`/api/places/festivals` 처럼 카테고리 전용 경로로 바로 호출할 수도 있습니다.

## 날씨 적합도 태그 (`tags` 파라미터에 쓰는 값)

{tag_docs_table()}

`tags=rain,indoor` 처럼 쉼표로 여러 개 넘기고 `match=any`(기본값, 하나만 맞아도 포함)
또는 `match=all`(전부 맞아야 포함)로 조합 방식을 고를 수 있습니다.
""".strip()

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 서버 애플리케이션 객체 생성


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


@app.on_event("startup")
def _seed_places_data() -> None:
    """서버 기동 시 TourAPI 장소 데이터를 자동으로 적재한다(upsert라 반복 실행해도 안전)."""
    db = SessionLocal()
    try:
        seed_places(db)
    finally:
        db.close()


@app.get("/api", tags=["health"], summary="헬스체크")
def health_check():
    """서버가 살아있는지 확인용. 인증 없이 누구나 호출 가능."""
    return {"status": "ok", "message": "LocalHub API is running"}
