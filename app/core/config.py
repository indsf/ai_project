import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./localhub.db")

# "openai" | "anthropic" — 팀 공식 OpenAI 키가 오면 .env에서 값만 바꾸면 전환됨
CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "anthropic")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
