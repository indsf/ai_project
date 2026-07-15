# app/modules/recommend/crud.py

# 날씨 관련 데이터베이스(읽기,쓰기) 담당 ->  DB저장

# app/modules/recommend/crud.py

from sqlalchemy.orm import Session

from app.modules.recommend.models import (
    WeatherForecast,
)


def save_weather_forecasts(
    db: Session,
    forecasts: list[dict],
) -> list[WeatherForecast]:
    """
    같은 지역·같은 예보 시각의 데이터는 갱신하고,
    없는 데이터는 새로 저장한다.
    """

    saved_forecasts: list[WeatherForecast] = []

    try:
        for data in forecasts:
            weather = (
                db.query(WeatherForecast)
                .filter(
                    WeatherForecast.nx
                    == data["nx"],
                    WeatherForecast.ny
                    == data["ny"],
                    WeatherForecast.forecast_at
                    == data["forecast_at"],
                )
                .first()
            )

            if weather is None:
                weather = WeatherForecast(
                    **data
                )
                db.add(weather)

            else:
                weather.base_datetime = data[
                    "base_datetime"
                ]
                weather.temperature = data[
                    "temperature"
                ]
                weather.rain_prob = data[
                    "rain_prob"
                ]
                weather.rain_type = data[
                    "rain_type"
                ]

            saved_forecasts.append(weather)

        db.commit()

        for weather in saved_forecasts:
            db.refresh(weather)

        return saved_forecasts

    except Exception:
        db.rollback()
        raise