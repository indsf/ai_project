# app/modules/recommend/models.py

# 안에서 SQLAlchemy를 이용해 SQLite 테이블 구조를 정의하는 파일(DB 구조)


# app/modules/recommend/models.py

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
    """
    기상청 단기예보 데이터를 시간대별로 저장하는 테이블
    """

    __tablename__ = "weather_forecasts"

    __table_args__ = (
        UniqueConstraint(
            "nx",
            "ny",
            "forecast_at",
            name="uq_weather_forecast_location_time",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 기상청 격자 좌표
    nx = Column(
        Integer,
        nullable=False,
        index=True,
    )

    ny = Column(
        Integer,
        nullable=False,
        index=True,
    )

    # 기상청 예보 발표 시각
    # baseDate + baseTime
    base_datetime = Column(
        DateTime,
        nullable=False,
    )

    # 실제 예보 대상 시각(예측 일자 + 예측 시간)
    # fcstDate + fcstTime
    forecast_at = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    # TMP(온도)
    temperature = Column(
        Float,
        nullable=True,
    )

    # POP(강수확률)
    rain_prob = Column(
        Integer,
        nullable=True,
    )

    # PTY 변환 결과
    # NONE, RAIN, RAIN_SNOW, SNOW, SHOWER
    rain_type = Column(
        String(20),
        nullable=False,
        default="NONE",
    )

    # 우리 DB에 저장된 시각
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )