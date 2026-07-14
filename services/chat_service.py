import os
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import Post

RAW_KEY = os.getenv("OPENAI_API_KEY", "")
IS_ANTHROPIC = RAW_KEY.startswith("sk-ant-")

if IS_ANTHROPIC:
    from anthropic import Anthropic
    client = Anthropic(api_key=RAW_KEY)
else:
    from openai import OpenAI
    client = OpenAI(api_key=RAW_KEY)


def get_festival_context(db: Session) -> tuple[str, list[int]]:
    today = date.today()
    posts = (
        db.query(Post)
        .filter(
            or_(
                Post.category == "spot",
                Post.end_date >= today,
                Post.end_date.is_(None),
            )
        )
        .limit(15)
        .all()
    )

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
    """OpenAI든 Anthropic이든 같은 인터페이스로 호출"""
    if IS_ANTHROPIC:
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
    else:
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