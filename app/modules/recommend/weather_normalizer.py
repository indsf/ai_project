# app/modules/recommend/weather_normalizer.py

# ex) 강수확률이 있다고 비 상태로 확정하면 데이터 불 일치 


def normalize_weather(
    temperature: float | None,
    rain_type: str,
) -> str:
    """
    DB에 저장된 기온과 강수형태를
    추천 알고리즘용 대표 날씨로 변환한다.
    """

    if rain_type == "SNOW":
        return "SNOW"

    if rain_type in {
        "RAIN",
        "RAIN_SNOW",
        "SHOWER",
    }:
        return "RAIN"

    if temperature is not None and temperature >= 33:
        return "HOT"

    if temperature is not None and temperature <= 0:
        return "COLD"

    return "NORMAL"