from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.modules.posts import models as posts_models  # Base.metadata에 테이블 등록되도록 import 필요
from app.modules.posts.router import router as posts_router
from app.modules.recommend.router import router as recommend_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LocalHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(posts_router)
app.include_router(recommend_router)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "LocalHub API is running"}
