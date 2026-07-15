# app/core/config.py

import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 읽는다.
load_dotenv()

# 장소 관련 data_read
PLACES_DATA_DIR = Path(
    os.getenv(
        "PLACES_DATA_DIR",
        str(Path(__file__).resolve().parent.parent / "data"),
    )
)

# 날씨 관련 api키
KMA_API_KEY = os.getenv("KMA_API_KEY")

if not KMA_API_KEY:
    raise RuntimeError(
        "KMA_API_KEY 환경변수가 설정되지 않았습니다. "
        "프로젝트 루트의 .env 파일을 확인하세요."
    )

# 챗봇 관련 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./localhub.db")

CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "anthropic")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")