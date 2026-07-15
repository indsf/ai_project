# app/modules/recommend/crud.py

from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.recommend.models import WeatherForecast


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


def save_weather_forecasts(
    db: Session,
    forecasts: list[dict],
) -> list[WeatherForecast]:
    """
    시간대별 예보를 저장한다.

    동일한 지역과 예보 시각이 없으면 INSERT하고,
    이미 존재하면 최신 발표 예보로 UPDATE한다.
    """

    saved_forecasts: list[WeatherForecast] = []

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
                    f"[INSERT] {data['forecast_at']}"
                )

                weather = WeatherForecast(**data)
                db.add(weather)

            else:
                weather.base_datetime = data["base_datetime"]
                weather.temperature = data["temperature"]
                weather.rain_prob = data["rain_prob"]
                weather.rain_type = data["rain_type"]
                weather.sky_type = data["sky_type"]

                changed = db.is_modified(
                    weather,
                    include_collections=False,
                )

                if changed:
                    print(
                        f"[UPDATE] {data['forecast_at']}"
                    )
                else:
                    print(
                        f"[UNCHANGED] {data['forecast_at']}"
                    )

            saved_forecasts.append(weather)

        db.commit()

        for weather in saved_forecasts:
            db.refresh(weather)

        return saved_forecasts

    except Exception:
        db.rollback()
        raise