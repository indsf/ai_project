# app/modules/recommend/crud.py


from datetime import datetime
from sqlalchemy.orm import Session
from app.modules.recommend.models import WeatherForecast
from app.modules.recommend.models import (
    WeatherForecast,
)

# 사용자 요청 -> 가장 가까운 예보를 가져오기 함수
def get_nearest_weather(
    db: Session,
    target_at: datetime,
) -> WeatherForecast | None:
    """
    target_at 이후의 예보 중 가장 가까운 예보를 조회한다.
    """

    return (
        db.query(WeatherForecast)
        .filter(
            WeatherForecast.forecast_at >= target_at,
        )
        .order_by(
            WeatherForecast.forecast_at.asc(),
        )
        .first()
    )

# 날씨 관련 데이터베이스(읽기,쓰기) 담당 ->  DB저장
def save_weather_forecasts(
    db: Session,
    forecasts: list[dict],
) -> list[WeatherForecast]:

    saved_forecasts = []

    try:
        for data in forecasts:
            weather = (
                db.query(WeatherForecast)
                .filter(
                    WeatherForecast.nx == data["nx"],
                    WeatherForecast.ny == data["ny"],
                    WeatherForecast.forecast_at
                    == data["forecast_at"],
                )
                .first()
            )

            if weather is None:
                print(
                    f"INSERT: {data['forecast_at']}"
                )

                weather = WeatherForecast(**data)
                db.add(weather)

            else:            
                print(
                    f"UPDATE 대상: {data['forecast_at']}"
                )

                weather.base_datetime = data["base_datetime"]
                weather.temperature = data["temperature"]
                weather.rain_prob = data["rain_prob"]
                weather.rain_type = data["rain_type"]

                if "normalized_weather" in data:
                    weather.normalized_weather = (
                        data["normalized_weather"]
                    )

                print(
                    "실제 변경 여부:",
                    db.is_modified(
                        weather,
                        include_collections=False,
                    ),
                )

            saved_forecasts.append(weather)

        db.commit()

        for weather in saved_forecasts:
            db.refresh(weather)

        return saved_forecasts

    except Exception:
        db.rollback()
        raise

