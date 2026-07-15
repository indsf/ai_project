# app/core/config.py

import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 읽는다.
load_dotenv()

# TourAPI 원본 데이터(8개 카테고리 JSON)가 들어있는 디렉터리. 기본값은 app/data.
# 파일명은 app/modules/places/categories.py의 CONTENT_TYPE_REGISTRY에서 관리한다.
PLACES_DATA_DIR = Path(
    os.getenv(
        "PLACES_DATA_DIR",
        str(Path(__file__).resolve().parent.parent / "data"),
    )
)
