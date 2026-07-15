# app/modules/recommend/chat_service.py

from sqlalchemy.orm import Session

from app.core.config import CHAT_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY
from app.modules.posts.service import get_post_context_for_chat
from app.modules.recommend.place_crud import (
    search_places,
    get_places_by_category,
    get_places_sample,
)
from app.modules.recommend import weather_crud, weather_service

if CHAT_PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)


CATEGORY_KEYWORDS = {
    "축제": "15",
    "공연": "15",
    "행사": "15",
    "관광지": "12",
    "관광": "12",
    "음식": "39",
    "맛집": "39",
    "먹거리": "39",
    "숙박": "32",
    "호텔": "32",
    "쇼핑": "38",
    "레포츠": "28",
    "액티비티": "28",
    "문화시설": "14",
    "여행코스": "25",
}

RAIN_TYPE_LABEL = {
    "NONE": "맑음",
    "RAIN": "비",
    "RAIN_SNOW": "비/눈",
    "SNOW": "눈",
    "SHOWER": "소나기",
}


def get_post_context(db: Session) -> tuple[str, list[int]]:
    """사용자가 작성한 커뮤니티 게시글(축제/관광/맛집 정보) 컨텍스트"""
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


def get_place_context(db: Session, message: str) -> str:
    """공공데이터(TourAPI) 기반 관광지/맛집/축제 정보 컨텍스트"""
    matched_type_id = None
    for kw, type_id in CATEGORY_KEYWORDS.items():
        if kw in message:
            matched_type_id = type_id
            break

    if matched_type_id:
        places = get_places_by_category(db, matched_type_id, limit=10)
    else:
        places = search_places(db, message, limit=10) or get_places_sample(db, limit=5)

    if not places:
        return "관련된 공공 관광정보를 찾지 못했습니다."

    lines = []
    for place in places:
        addr = place.addr1 or "주소 미정"
        lines.append(f"- {place.title} / {addr} / 전화: {place.tel or '정보 없음'}")

    return "\n".join(lines)


def get_weather_context(db: Session) -> str:
    """구미 지역 최신 단기예보 컨텍스트"""
    forecasts = weather_crud.get_forecasts(
        db=db,
        nx=weather_service.DEFAULT_NX,
        ny=weather_service.DEFAULT_NY,
        limit=8,
    )

    if not forecasts:
        return "현재 저장된 날씨 예보 데이터가 없습니다."

    lines = []
    for f in forecasts:
        time_label = f.forecast_at.strftime("%m/%d %H시")
        rain_label = RAIN_TYPE_LABEL.get(f.rain_type, f.rain_type)
        lines.append(f"- {time_label}: 기온 {f.temperature}℃, 강수확률 {f.rain_prob}%, {rain_label}")

    return "\n".join(lines)


def call_llm(system_prompt: str, history: list, message: str) -> str:
    """CHAT_PROVIDER가 openai든 anthropic이든 같은 인터페이스로 호출"""
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
    place_context = get_place_context(db, message)
    weather_context = get_weather_context(db)

    system_prompt = f"""너는 구미 지역 정보 커뮤니티 'LocalHub'의 안내 챗봇이야.

세 가지 정보를 참고해서 사용자 질문에 답해줘:

[사용자 게시글 - 축제/관광/맛집 정보]
{post_context}

[공공데이터 - 관광지/맛집/축제 정보]
{place_context}

[구미 지역 날씨 예보]
{weather_context}

답변 작성 규칙:
- 마크다운 문법(#, ##, **, -, 1. 등)을 절대 쓰지 마. 순수 텍스트 문장으로만 답해.
- 목록을 보여줄 때도 기호나 번호 없이, "첫 번째로는 ~, 두 번째로는 ~" 처럼 자연스러운 문장으로 이어서 말해.
- 친근하고 편안한 대화체로 답해. 너무 딱딱하거나 사무적으로 말하지 마.
- 날씨를 물어보면 위 [구미 지역 날씨 예보]를 참고해서 답해줘. 비/눈 예보가 있으면 실내 활동(관광지/맛집)을, 맑으면 야외 활동(축제/관광지)을 자연스럽게 같이 추천해줘.
- 이동 거리나 소요 시간은 정확한 정보가 없으니 추측해서 답하지 말고, "정확한 이동 시간은 지도 앱으로 확인해보시는 걸 추천해요"라고 안내해줘.
- 목록에 없는 내용은 추측하지 말고 "그 정보는 아직 등록되어 있지 않아요"라고 자연스럽게 안내해.
- 답변은 3~5문장 정도로 간결하게 정리해줘.
"""

    reply = call_llm(system_prompt, history, message)
    return reply, post_ids[:3]