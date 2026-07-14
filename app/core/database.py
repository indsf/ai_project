# app/core/database.py
# 공용 DB 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite DB 파일을 프로젝트 최상단에 app.db 라는 이름으로 생성합니다.
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# SQLite는 기본적으로 단일 스레드만 허용하므로, FastAPI(다중 스레드)에서 쓰기 위한 옵션 추가
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 라우터에서 DB 세션을 안전하게 열고 닫기 위한 의존성 주입(Dependency Injection) 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()