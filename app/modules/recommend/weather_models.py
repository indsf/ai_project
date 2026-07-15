# app/modules/recommend/weather_models.py

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.core.database import Base


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    __table_args__ = (
        UniqueConstraint("nx", "ny", "forecast_at", name="uq_weather_forecast_location_time"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    nx = Column(Integer, nullable=False, index=True)
    ny = Column(Integer, nullable=False, index=True)
    base_datetime = Column(DateTime, nullable=False)
    forecast_at = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=True)
    rain_prob = Column(Integer, nullable=True)
    rain_type = Column(String(20), nullable=False, default="NONE")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())