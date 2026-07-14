# app/core/config.py

import os

from dotenv import load_dotenv


# 프로젝트 루트의 .env 파일을 읽는다.
load_dotenv()


KMA_API_KEY = os.getenv("KMA_API_KEY")

if not KMA_API_KEY:
    raise RuntimeError(
        "KMA_API_KEY 환경변수가 설정되지 않았습니다. "
        "프로젝트 루트의 .env 파일을 확인하세요."
    )