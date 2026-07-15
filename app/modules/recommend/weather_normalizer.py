# app/modules/recommend/weather_normalizer.py

def normalize_weather(
    temperature: float | None,
    rain_prob: int | None,
    rain_type: str,
    sky_type: str,
) -> str:
    """
    DB에 저장된 예보 정보를 추천 알고리즘용 대표 날씨로 변환한다.
    """
    if rain_type == "SNOW":
        return "SNOW"

    if rain_type in {"RAIN", "RAIN_SNOW", "SHOWER"}:
        return "RAIN"

    if rain_prob is not None and rain_prob >= 60:
        return "RAIN"

    if temperature is not None and temperature >= 33:
        return "HOT"

    if temperature is not None and temperature <= 0:
        return "COLD"

    if sky_type == "CLEAR":
        return "SUNNY"

    return "NORMAL"


def weather_to_place_tags(normalized_weather: str) -> list[str]:
    """대표 날씨를 Places API 검색용 태그로 변환한다."""
    tag_mapping = {
        "SNOW": ["rain", "cold", "indoor"],
        "RAIN": ["rain", "indoor"],
        "HOT": ["hot"],
        "COLD": ["cold"],
        "SUNNY": ["sunny"],
        "NORMAL": ["outdoor"],
    }
    return tag_mapping.get(normalized_weather, ["outdoor"])