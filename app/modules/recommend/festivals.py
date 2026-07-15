# app/modules/recommend/festival.py

from sqlalchemy.orm import Session

from app.modules.places.service import (
    PlaceSummary,
    get_places_for_recommendation,
)
from app.modules.recommend.service import (
    get_current_weather_context,
)


def calculate_festival_score(
    festival: PlaceSummary,
    weather_tags: list[str],
    normalized_weather: str,
) -> tuple[int, list[str]]:
    """
    현재 날씨와 축제의 날씨 적합도 태그를 비교해
    추천 점수와 추천 사유를 계산한다.
    """

    score = 0
    reasons: list[str] = []

    festival_tags = set(festival.tags or [])
    current_weather_tags = set(weather_tags)

    # 1. 현재 날씨 태그와 축제 태그 일치
    matched_tags = (
        current_weather_tags
        & festival_tags
    )

    if matched_tags:
        tag_score = len(matched_tags) * 50
        score += tag_score

        reasons.append(
            "현재 날씨 태그와 일치: "
            + ", ".join(sorted(matched_tags))
        )

    # 2. 맑은 날 야외 축제 우선
    if (
        normalized_weather == "SUNNY"
        and "outdoor" in festival_tags
    ):
        score += 20
        reasons.append(
            "맑은 날 야외 활동에 적합"
        )

    # 3. 비 오는 날 실내형 축제 우선
    if (
        normalized_weather == "RAIN"
        and "indoor" in festival_tags
    ):
        score += 20
        reasons.append(
            "비 오는 날 이용 가능한 실내형 장소"
        )

    # 4. 더운 날 적합 장소
    if (
        normalized_weather == "HOT"
        and "hot" in festival_tags
    ):
        score += 20
        reasons.append(
            "더운 날 이용하기 적합"
        )

    # 5. 추운 날 적합 장소
    if (
        normalized_weather
        in {"COLD", "SNOW"}
        and "cold" in festival_tags
    ):
        score += 20
        reasons.append(
            "추운 날 이용하기 적합"
        )

    # 6. 구미 지역 축제 우선
    address = festival.addr1 or ""

    if "구미" in address:
        score += 20
        reasons.append(
            "구미 지역 축제"
        )

    # 7. 사용자 위치가 있는 경우 거리 점수
    if festival.distance_km is not None:
        if festival.distance_km <= 5:
            score += 20
            reasons.append(
                "현재 위치에서 5km 이내"
            )

        elif festival.distance_km <= 15:
            score += 10
            reasons.append(
                "현재 위치에서 15km 이내"
            )

    return score, reasons


def get_festival_recommendations(
    db: Session,
    lat: float | None = None,
    lng: float | None = None,
    limit: int = 10,
) -> dict:
    """
    현재 날씨를 조회하고 날씨에 맞는 축제를 가져온 뒤
    추천 점수를 계산해 높은 점수순으로 반환한다.
    """

    if (lat is None) != (lng is None):
        raise ValueError(
            "lat과 lng는 함께 전달해야 합니다."
        )

    # 1. 현재 날씨 조회 및 정규화
    weather_context = (
        get_current_weather_context(db)
    )

    weather_tags = weather_context[
        "place_tags"
    ]

    normalized_weather = weather_context[
        "normalized_weather"
    ]

    # 2. 현재 날씨 태그에 맞는 축제 조회
    #
    # 내부적으로 다음 조건과 동일하다.
    # category=festivals
    # tags=sunny
    # match=any
    festivals = get_places_for_recommendation(
        db=db,
        categories=["festivals"],
        tags=weather_tags,
        match="any",
        lat=lat,
        lng=lng,

        # 점수 계산 후 상위 limit개를 고르기 위해
        # 후보를 넉넉하게 조회한다.
        limit=100,
    )

    # 3. 축제별 추천 점수 계산
    scored_festivals: list[dict] = []

    for festival in festivals:
        score, reasons = (
            calculate_festival_score(
                festival=festival,
                weather_tags=weather_tags,
                normalized_weather=(
                    normalized_weather
                ),
            )
        )

        scored_festivals.append(
            {
                "content_id": (
                    festival.content_id
                ),
                "category": festival.category,
                "title": festival.title,
                "addr1": festival.addr1,
                "image_url": (
                    festival.image_url
                ),
                "tags": festival.tags,
                "distance_km": (
                    festival.distance_km
                ),
                "recommendation_score": (
                    score
                ),
                "recommendation_reasons": (
                    reasons
                ),
            }
        )

    # 4. 추천 점수가 높은 순서대로 정렬
    #
    # 점수가 같고 거리 정보가 있으면
    # 가까운 장소를 먼저 정렬한다.
    scored_festivals.sort(
        key=lambda item: (
            -item["recommendation_score"],
            (
                item["distance_km"]
                if item["distance_km"]
                is not None
                else float("inf")
            ),
            item["title"],
        )
    )

    # 5. 상위 결과만 반환
    recommended_items = (
        scored_festivals[:limit]
    )

    return {
        "weather": {
            "forecast_at": (
                weather_context["forecast_at"]
            ),
            "temperature": (
                weather_context["temperature"]
            ),
            "rain_prob": (
                weather_context["rain_prob"]
            ),
            "rain_type": (
                weather_context["rain_type"]
            ),
            "sky_type": (
                weather_context["sky_type"]
            ),
            "normalized_weather": (
                normalized_weather
            ),
        },
        "applied_tags": weather_tags,
        "candidate_count": len(festivals),
        "recommendation_count": len(
            recommended_items
        ),
        "items": recommended_items,
    }


if __name__ == "__main__":
    from app.core.database import (
        SessionLocal,
    )

    db = SessionLocal()

    try:
        result = get_festival_recommendations(
            db=db,
            limit=10,
        )

        print("============================")
        print("현재 날씨 기반 축제 추천")
        print("============================")

        print(
            "추천용 날씨:",
            result["weather"][
                "normalized_weather"
            ],
        )

        print(
            "적용 태그:",
            result["applied_tags"],
        )

        print(
            "추천 후보 수:",
            result["candidate_count"],
        )

        for index, festival in enumerate(
            result["items"],
            start=1,
        ):
            print("----------------------------")
            print(
                f"{index}위: "
                f"{festival['title']}"
            )
            print(
                "주소:",
                festival["addr1"],
            )
            print(
                "태그:",
                festival["tags"],
            )
            print(
                "추천 점수:",
                festival[
                    "recommendation_score"
                ],
            )
            print(
                "추천 사유:",
                festival[
                    "recommendation_reasons"
                ],
            )

    finally:
        db.close()