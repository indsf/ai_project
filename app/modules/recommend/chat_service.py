# app/modules/recommend/chat_service.py

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import CHAT_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY
from app.modules.posts.service import get_post_context_for_chat
from app.modules.places.service import get_places_for_recommendation
from app.modules.recommend.service import get_current_weather_context, DEFAULT_NX, DEFAULT_NY
from app.modules.recommend.weather_normalizer import weather_to_place_tags
from app.modules.recommend import crud as weather_crud

if CHAT_PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)


CATEGORY_KEYWORDS = {
    "축제": "festivals",
    "공연": "festivals",
    "행사": "festivals",
    "관광지": "attractions",
    "관광": "attractions",
    "음식": "restaurants",
    "맛집": "restaurants",
    "먹거리": "restaurants",
    "숙박": "lodging",
    "호텔": "lodging",
    "쇼핑": "shopping",
    "레포츠": "leisure",
    "액티비티": "leisure",
    "문화시설": "culture",
    "여행코스": "courses",
}

RAIN_TYPE_LABEL = {
    "NONE": "맑음",
    "RAIN": "비",
    "RAIN_SNOW": "비/눈",
    "SNOW": "눈",
    "SHOWER": "소나기",
}


def get_post_context(db: Session) -> tuple[str, list[int]]:
    """사용자가 작성한 커뮤니티 게시글 컨텍스트"""
    posts = get_post_context_for_chat(db)

    if not posts:
        return "현재 등록된 게시글이 없습니다.", []

    lines = []
    ids = []

    for p in posts:
        period = f" ({p.start_date}~{p.end_date})" if p.start_date else ""
        lines.append(f"- [{p.id}] {p.title} / {p.category} / {p.location or '위치 미정'}{period}")
        ids.append(p.id)

    return "\n".join(lines), ids


def get_weather_context(db: Session) -> tuple[str, str | None]:
    """구미 지역 향후 7일 날씨 컨텍스트. (텍스트, 현재 시점 정규화 날씨) 반환."""
    now_kst = datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)
    forecasts = weather_crud.get_forecasts_range(db, DEFAULT_NX, DEFAULT_NY, now_kst, days=7)

    if not forecasts:
        return "현재 저장된 날씨 예보 데이터가 없습니다.", None

    by_date: dict[str, list] = {}
    for f in forecasts:
        date_key = f.forecast_at.strftime("%m/%d")
        by_date.setdefault(date_key, []).append(f)

    lines = []
    for date_key, day_forecasts in by_date.items():
        rain_forecasts = [f for f in day_forecasts if f.rain_type != "NONE"]
        temps = [f.temperature for f in day_forecasts if f.temperature is not None]
        max_temp = max(temps) if temps else None
        min_temp = min(temps) if temps else None

        if rain_forecasts:
            rain_hours = ", ".join(f.forecast_at.strftime("%H시") for f in rain_forecasts)
            rain_label = RAIN_TYPE_LABEL.get(rain_forecasts[0].rain_type, rain_forecasts[0].rain_type)
            lines.append(f"- {date_key}: 최고 {max_temp}℃/최저 {min_temp}℃, {rain_hours}에 {rain_label} 예보")
        else:
            lines.append(f"- {date_key}: 최고 {max_temp}℃/최저 {min_temp}℃, 비 소식 없음")

    text = "\n".join(lines)

    try:
        current = get_current_weather_context(db)
        normalized = current["normalized_weather"]
    except ValueError:
        normalized = None

    return text, normalized


def get_place_context(db: Session, message: str, normalized_weather: str | None) -> str:
    """장소(TourAPI) + 현재 날씨 태그 기반 추천 컨텍스트"""
    matched_slug = None
    for kw, slug in CATEGORY_KEYWORDS.items():
        if kw in message:
            matched_slug = slug
            break

    weather_tags = weather_to_place_tags(normalized_weather) if normalized_weather else None

    places = get_places_for_recommendation(
        db,
        categories=[matched_slug] if matched_slug else None,
        tags=weather_tags,
        limit=10,
    )

    if not places:
        return "관련된 공공 관광정보를 찾지 못했습니다."

    lines = []
    for place in places:
        addr = place.addr1 or "주소 미정"
        lines.append(f"- {place.title} / {addr}")

    return "\n".join(lines)


def call_llm(system_prompt: str, history: list, message: str) -> str:
    if CHAT_PROVIDER == "openai":
        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            timeout=15,
        )
        return response.choices[0].message.content
    else:
        messages = []
        for h in history:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": message})

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=system_prompt,
            messages=messages,
            timeout=15,
        )
        return response.content[0].text


def get_chat_response(message: str, history: list, db: Session) -> tuple[str, list[int]]:
    post_context, post_ids = get_post_context(db)
    weather_text, normalized_weather = get_weather_context(db)
    place_context = get_place_context(db, message, normalized_weather)

    system_prompt = f"""너는 구미 지역 정보 커뮤니티 'LocalHub'의 안내 챗봇이야.

세 가지 정보를 참고해서 사용자 질문에 답해줘:

[사용자 게시글 - 축제/관광/맛집 정보]
{post_context}

[구미 지역 향후 7일 날씨]
{weather_text}

[장소 추천 정보 - 현재 날씨에 맞춰 필터링됨]
{place_context}

답변 작성 규칙:
- 마크다운 문법(#, ##, **, -, 1. 등)을 절대 쓰지 마. 순수 텍스트 문장으로만 답해.
- 목록을 보여줄 때도 기호나 번호 없이 자연스러운 문장으로 이어서 말해.
- 친근하고 편안한 대화체로 답해.
- 날씨를 물어보면 [구미 지역 향후 7일 날씨]를 참고해서 답해줘. 특정 날짜를 물어보면 해당 날짜 줄을 찾아서 답하고, "이번주 비오는 날" 같은 질문엔 목록에서 비 예보 있는 날짜만 추려서 답해줘.
- 장소를 추천할 땐 이미 현재 날씨에 맞게 걸러진 목록이니, 그 이유(비 와서 실내 위주 등)를 자연스럽게 곁들여줘.
- 이동 거리나 소요 시간은 정확한 정보가 없으니 "정확한 이동 시간은 지도 앱으로 확인해보시는 걸 추천해요"라고 안내해줘.
- 목록에 없는 내용은 추측하지 말고 "그 정보는 아직 등록되어 있지 않아요"라고 안내해.
- 답변은 3~5문장 정도로 간결하게.
"""

    reply = call_llm(system_prompt, history, message)
    return reply, post_ids[:3]