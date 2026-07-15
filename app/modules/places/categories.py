# app/modules/places/categories.py
#
# TourAPI contentTypeId <-> URL 슬러그 <-> 원본 데이터 파일 매핑.
# 새 카테고리를 추가할 땐 이 딕셔너리에 한 줄만 추가하면 seed도, 라우터도 자동으로 따라온다.

from typing import TypedDict


class CategoryMeta(TypedDict):
    slug: str
    label: str
    file: str


CONTENT_TYPE_REGISTRY: dict[str, CategoryMeta] = {
    "12": {"slug": "attractions", "label": "관광지", "file": "구미_경북권_관광지.json"},
    "14": {"slug": "culture", "label": "문화시설", "file": "구미_경북권_문화시설.json"},
    "15": {"slug": "festivals", "label": "축제공연행사", "file": "구미_경북권_축제공연행사.json"},
    "25": {"slug": "courses", "label": "여행코스", "file": "구미_경북권_여행코스.json"},
    "28": {"slug": "leisure", "label": "레포츠", "file": "구미_경북권_레포츠.json"},
    "32": {"slug": "lodging", "label": "숙박", "file": "구미_경북권_숙박.json"},
    "38": {"slug": "shopping", "label": "쇼핑", "file": "구미_경북권_쇼핑.json"},
    "39": {"slug": "restaurants", "label": "음식점", "file": "구미_경북권_음식점.json"},
}

SLUG_TO_CONTENT_TYPE: dict[str, str] = {
    meta["slug"]: content_type_id for content_type_id, meta in CONTENT_TYPE_REGISTRY.items()
}


def slug_for(content_type_id: str) -> str:
    meta = CONTENT_TYPE_REGISTRY.get(str(content_type_id))
    return meta["slug"] if meta else "unknown"


def category_docs_table() -> str:
    """API 문서용 마크다운 표. 카테고리 추가/삭제 시 자동으로 같이 갱신된다."""
    rows = "\n".join(
        f"| `{meta['slug']}` | {meta['label']} |"
        for meta in CONTENT_TYPE_REGISTRY.values()
    )
    return "| category 값 | 의미 |\n|---|---|\n" + rows


def category_slugs_csv() -> str:
    """Query 파라미터 설명에 넣을 슬러그 나열 문자열. 예: 'attractions, culture, festivals, ...'"""
    return ", ".join(meta["slug"] for meta in CONTENT_TYPE_REGISTRY.values())
