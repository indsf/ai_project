import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./localhub.db")

# "openai" | "anthropic" — 팀 공식 OpenAI 키가 오면 .env에서 값만 바꾸면 전환됨
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "anthropic")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# 기상청 단기예보 API 인증키
KMA_API_KEY = os.getenv("KMA_API_KEY", "")

# 축제 데이터(TourAPI) 시드 파일 경로
FESTIVAL_DATA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data" / "tourapi" / "구미_경북권_축제공연행사.json"
)