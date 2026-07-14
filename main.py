from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import chat
import models  # Base.metadata에 테이블 등록되도록 import 필요

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LocalHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "LocalHub API is running"}