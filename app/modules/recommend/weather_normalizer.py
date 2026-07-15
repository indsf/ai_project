
# 날씨 정규화
def normalize_weather(
    temperature: float | None,
    rain_prob: int | None,
    rain_type: str,
    sky_type: str,
) -> str:
    """
    DB에 저장된 예보 정보를
    추천 알고리즘용 대표 날씨로 변환한다.
    """

    # 눈 예보
    if rain_type == "SNOW":
        return "SNOW"

    # 비, 진눈깨비, 소나기 예보
    if rain_type in {
        "RAIN",
        "RAIN_SNOW",
        "SHOWER",
    }:
        return "RAIN"

    # 현재 강수형태는 없지만 비 올 가능성이 높은 경우
    if (
        rain_prob is not None
        and rain_prob >= 60
    ):
        return "RAIN"

    # 더운 날
    if (
        temperature is not None
        and temperature >= 33
    ):
        return "HOT"

    # 추운 날
    if (
        temperature is not None
        and temperature <= 0
    ):
        return "COLD"

    # 맑은 날
    if sky_type == "CLEAR":
        return "SUNNY"

    # 비는 없지만 구름이 많거나 흐린 날
    return "NORMAL"


# 날씨별 장소 태그 
def weather_to_place_tags(
    normalized_weather: str,
) -> list[str]:
    """
    대표 날씨를 Places API 검색용 태그로 변환한다.
    """

    tag_mapping = {
        "SNOW": [
            "rain",
            "cold",
            "indoor",
        ],
        "RAIN": [
            "rain",
            "indoor",
        ],
        "HOT": [
            "hot",
        ],
        "COLD": [
            "cold",
        ],
        "SUNNY": [
            "sunny",
        ],
        "NORMAL": [
            "outdoor",
        ],
    }

    return tag_mapping.get(
        normalized_weather,
        ["outdoor"],
    )