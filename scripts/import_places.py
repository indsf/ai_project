# scripts/import_places.py
# TourAPI JSON 8개 파일을 읽어서 DB에 저장

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.database import Base, SessionLocal, engine
from app.modules.recommend.place_models import Place
from app.modules.recommend import place_crud

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "tourapi"

FILES = [
    "구미_경북권_관광지.json",
    "구미_경북권_레포츠.json",
    "구미_경북권_문화시설.json",
    "구미_경북권_쇼핑.json",
    "구미_경북권_숙박.json",
    "구미_경북권_여행코스.json",
    "구미_경북권_음식점.json",
    "구미_경북권_축제공연행사.json",
]


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def import_all():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    total_saved = 0

    try:
        for filename in FILES:
            filepath = DATA_DIR / filename

            if not filepath.exists():
                print(f"[건너뜀] 파일 없음: {filepath}")
                continue

            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)

            items = data.get("items", [])
            print(f"{filename}: {len(items)}건 처리 중...")

            for item in items:
                place_data = {
                    "content_id": item.get("contentid"),
                    "content_type_id": item.get("contenttypeid"),
                    "title": item.get("title", ""),
                    "addr1": item.get("addr1") or None,
                    "addr2": item.get("addr2") or None,
                    "tel": item.get("tel") or None,
                    "mapx": to_float(item.get("mapx")),
                    "mapy": to_float(item.get("mapy")),
                    "area_code": item.get("areacode") or None,
                    "sigungu_code": item.get("sigungucode") or None,
                    "cat1": item.get("cat1") or None,
                    "cat2": item.get("cat2") or None,
                    "cat3": item.get("cat3") or None,
                    "first_image": item.get("firstimage") or None,
                }

                if not place_data["content_id"]:
                    continue

                place_crud.upsert_place(db, place_data)
                total_saved += 1

            db.commit()

        print(f"완료: 총 {total_saved}건 저장")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_all()