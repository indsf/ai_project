# app/core/weather_tags.py
#
# TourAPI 원본 데이터(관광지/레포츠/문화시설/쇼핑/숙박/여행코스/음식점/축제공연행사)에
# "이 장소가 어떤 날씨에 가기 좋은지" 태그를 자동으로 붙이기 위한 규칙 기반 MVP 태거.
#
# 원본 데이터에는 실내/실외 여부가 필드로 없어서, 제목 키워드 + contentTypeId 기본값으로
# 추론한다. 100% 정확하진 않지만 MVP 단계에서 "대략 맞는" 태그를 빠르게 전체 데이터에
# 적용하기 위한 휴리스틱이다. 잘못 태깅된 항목은 나중에 개별적으로 고칠 수 있게
# tags 필드는 원본 필드를 건드리지 않고 "추가"만 한다 (공공누리 3유형 변경금지 조건 준수).

from typing import Iterable

# 태그 어휘 (MVP 최소 셋)
# - indoor / outdoor : 장소의 기본 성격
# - rain   : 비/악천후에도 갈만한 곳 (기본적으로 indoor에 부여)
# - hot    : 더운 날 가기 좋은 곳 (indoor 전체 + 계곡/워터파크 등 야외 물놀이)
# - cold   : 추운 날 가기 좋은 곳 (indoor 전체 + 온천/찜질방 등)
# - sunny  : 맑고 화창할 때 가기 좋은 야외 명소
# - any_weather : 날씨 상관없이 항상 갈만한 곳 (숙박)

CONTENT_TYPE_DEFAULT = {
    "12": "outdoor",  # 관광지 - 자연/유적 등 야외 비중이 높음
    "14": "indoor",   # 문화시설 - 박물관/미술관/공연장 등 대부분 실내
    "15": "outdoor",  # 축제공연행사 - 야외 개최가 많음
    "25": "outdoor",  # 여행코스 - 도보/드라이브 코스
    "28": "outdoor",  # 레포츠 - 캠핑/승마/골프 등 야외 비중이 높음
    "32": "indoor",   # 숙박 - 실내, 날씨 무관
    "38": "outdoor",  # 쇼핑 - 이 데이터셋은 전통시장 비중이 커서 야외 기본값
    "39": "indoor",   # 음식점 - 실내
}

INDOOR_KEYWORDS = [
    "박물관", "미술관", "전시관", "과학관", "도서관", "문고", "책방", "서점",
    "공연장", "콘서트하우스", "극장", "영화관", "아트홀", "문화예술회관", "체험관",
    "아쿠아리움", "실내",
    "몰", "백화점", "아울렛", "마트", "이마트", "홈플러스", "롯데", "하이마트",
    "스토어", "샵", "전자", "안경", "올리브영", "스파오", "다이소", "약국",
    "카페", "레스토랑", "식당", "고깃집", "국수", "쭈꾸미", "갈비", "순두부",
    "중화요리", "커피", "와인", "정육", "분식", "베이커리", "빵집",
    "찜질방", "사우나", "온천", "스케이트장", "볼링", "당구", "헬스", "PC방",
    "호텔", "모텔", "펜션", "스테이", "리조트", "유스호스텔", "콘도", "게스트하우스",
]

OUTDOOR_KEYWORDS = [
    "공원", "생태공원", "습지", "체육공원", "전망대", "저수지", "도립공원",
    "수목원", "휴양림", "야영장", "캠핑장", "오토캠핑장", "계곡", "해수욕장",
    "해변", "낙동강", "광장", "고분군", "서원", "향교", "유적지",
    "인라인스케이트장", "골프장", "CC", "농원", "낚시터", "둘레길", "등산",
    "야시장", "시장",
]

# hot/cold 보정용 키워드 (기본 태그 위에 추가로 얹는다)
HOT_EXTRA_KEYWORDS = ["계곡", "해수욕장", "물놀이", "워터파크", "수영장", "야영장", "캠핑장"]
COLD_EXTRA_KEYWORDS = ["온천", "찜질방", "사우나", "스케이트장"]


def _match_any(title: str, keywords: Iterable[str]) -> bool:
    return any(keyword in title for keyword in keywords)


def infer_tags(title: str, content_type_id: str) -> list[str]:
    """
    제목과 contentTypeId만으로 날씨 적합도 태그를 추론한다 (MVP 휴리스틱).

    우선순위: 제목 키워드 매칭 > contentTypeId 기본값
    """

    title = title or ""
    content_type_id = str(content_type_id) if content_type_id is not None else ""

    if _match_any(title, INDOOR_KEYWORDS):
        base = "indoor"
    elif _match_any(title, OUTDOOR_KEYWORDS):
        base = "outdoor"
    else:
        base = CONTENT_TYPE_DEFAULT.get(content_type_id, "outdoor")

    tags: set[str] = set()

    if base == "indoor":
        tags |= {"indoor", "rain", "hot", "cold"}
    else:
        tags |= {"outdoor", "sunny"}

    # 숙박은 실내+날씨무관으로 고정 (키워드 매칭 결과와 무관하게 덮어씀)
    if content_type_id == "32":
        tags = {"indoor", "any_weather", "rain", "hot", "cold"}

    if _match_any(title, HOT_EXTRA_KEYWORDS):
        tags.add("hot")

    if _match_any(title, COLD_EXTRA_KEYWORDS):
        tags.add("cold")

    return sorted(tags)


def encode_tags(tags: Iterable[str]) -> str:
    """DB에 저장할 정규화 문자열로 변환한다. 예: ['indoor','rain'] -> ',indoor,rain,'"""
    unique_sorted = sorted(set(t.strip() for t in tags if t and t.strip()))
    if not unique_sorted:
        return ""
    return "," + ",".join(unique_sorted) + ","


def decode_tags(raw: str | None) -> list[str]:
    """DB에 저장된 정규화 문자열을 리스트로 변환한다."""
    if not raw:
        return []
    return [t for t in raw.split(",") if t]
