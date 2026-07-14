from sqlalchemy.orm import Session
from app.core.config import CHAT_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEY
from app.modules.posts.service import get_post_context_for_chat

if CHAT_PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)


def get_festival_context(db: Session) -> tuple[str, list[int]]:
    posts = get_post_context_for_chat(db)

    if not posts:
        return "현재 등록된 축제·관광지 정보가 없습니다.", []

    lines = []
    ids = []
    for p in posts:
        period = f" ({p.start_date}~{p.end_date})" if p.start_date else ""
        lines.append(f"- [{p.id}] {p.title} / {p.category} / {p.location or '위치 미정'}{period}")
        ids.append(p.id)

    return "\n".join(lines), ids


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
    context, post_ids = get_festival_context(db)

    system_prompt = f"""너는 구미시 지역정보 커뮤니티 'LocalHub'의 안내 챗봇이야.
아래는 현재 DB에 등록된 구미 지역 축제·관광지 목록이야. 이 정보를 참고해서 사용자 질문에 답해줘.
목록에 없는 내용은 추측하지 말고 "해당 정보는 아직 등록되어 있지 않아요"라고 답해.

[구미 축제·관광지 목록]
{context}
"""
    reply = call_llm(system_prompt, history, message)
    return reply, post_ids[:3]
