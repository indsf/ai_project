# app/modules/recommend/weather_crud.py

from datetime import datetime
from sqlalchemy.orm import Session

from app.modules.recommend.weather_models import WeatherForecast


def save_weather_forecasts(db: Session, forecasts: list[dict]) -> list[WeatherForecast]:
    saved_forecasts: list[WeatherForecast] = []
    try:
        for data in forecasts:
            weather = (
                db.query(WeatherForecast)
                .filter(
                    WeatherForecast.nx == data["nx"],
                    WeatherForecast.ny == data["ny"],
                    WeatherForecast.forecast_at == data["forecast_at"],
                )
                .first()
            )
            if weather is None:
                weather = WeatherForecast(**data)
                db.add(weather)
            else:
                weather.base_datetime = data["base_datetime"]
                weather.temperature = data["temperature"]
                weather.rain_prob = data["rain_prob"]
                weather.rain_type = data["rain_type"]
            saved_forecasts.append(weather)
        db.commit()
        for weather in saved_forecasts:
            db.refresh(weather)
        return saved_forecasts
    except Exception:
        db.rollback()
        raise


def get_forecasts(db: Session, nx: int, ny: int, limit: int = 8) -> list[WeatherForecast]:
    return (
        db.query(WeatherForecast)
        .filter(
            WeatherForecast.nx == nx,
            WeatherForecast.ny == ny,
            WeatherForecast.forecast_at >= datetime.now(),
        )
        .order_by(WeatherForecast.forecast_at.asc())
        .limit(limit)
        .all()
    )