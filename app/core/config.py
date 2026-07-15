# app/core/config.py

import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 읽는다.
load_dotenv()

# 축제 원본 데이터(TourAPI) 위치. 기본값은 app/data 폴더 안의 파일.
FESTIVAL_DATA_PATH = Path(
    os.getenv(
        "FESTIVAL_DATA_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "구미_경북권_축제공연행사.json"),
    )
)
