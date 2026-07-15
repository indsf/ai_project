# app/modules/recommend/weather_service.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.recommend import weather_crud, weather_client


DEFAULT_NX = 84
DEFAULT_NY = 96

BASE_TIMES = [2, 5, 8, 11, 14, 17, 20, 23]

RAIN_TYPE_MAP = {
    "0": "NONE",
    "1": "RAIN",
    "2": "RAIN_SNOW",
    "3": "SNOW",
    "4": "SHOWER",
}


def get_latest_base_date_time(now: datetime | None = None) -> tuple[str, str]:
    korea_timezone = ZoneInfo("Asia/Seoul")

    if now is None:
        current_time = datetime.now(korea_timezone)
    elif now.tzinfo is None:
        current_time = now.replace(tzinfo=korea_timezone)
    else:
        current_time = now.astimezone(korea_timezone)

    for hour in reversed(BASE_TIMES):
        available_at = current_time.replace(hour=hour, minute=10, second=0, microsecond=0)
        if current_time >= available_at:
            return current_time.strftime("%Y%m%d"), f"{hour:02d}00"

    previous_day = current_time - timedelta(days=1)
    return previous_day.strftime("%Y%m%d"), "2300"


def parse_weather_items(
    items: list[dict[str, Any]],
    *,
    nx: int,
    ny: int,
    base_date: str,
    base_time: str,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = defaultdict(dict)

    for item in items:
        category = item.get("category")
        forecast_date = item.get("fcstDate")
        forecast_time = item.get("fcstTime")
        forecast_value = item.get("fcstValue")

        if category not in {"TMP", "POP", "PTY"}:
            continue
        if not forecast_date or not forecast_time:
            continue

        key = (str(forecast_date), str(forecast_time).zfill(4))
        grouped[key][category] = forecast_value

    base_datetime = datetime.strptime(f"{base_date}{base_time}", "%Y%m%d%H%M")

    forecasts: list[dict[str, Any]] = []

    for (forecast_date, forecast_time), values in sorted(grouped.items()):
        required_categories = {"TMP", "POP", "PTY"}
        if not required_categories.issubset(values):
            continue

        forecast_at = datetime.strptime(f"{forecast_date}{forecast_time}", "%Y%m%d%H%M")
        temperature = to_float(values.get("TMP"))
        rain_prob = to_int(values.get("POP"))
        raw_rain_type = str(values.get("PTY", "0"))
        rain_type = RAIN_TYPE_MAP.get(raw_rain_type, "UNKNOWN")

        forecasts.append({
            "nx": nx,
            "ny": ny,
            "base_datetime": base_datetime,
            "forecast_at": forecast_at,
            "temperature": temperature,
            "rain_prob": rain_prob,
            "rain_type": rain_type,
        })

    return forecasts


async def process_and_save_weather(
    db: Session,
    nx: int = DEFAULT_NX,
    ny: int = DEFAULT_NY,
    base_date: str | None = None,
    base_time: str | None = None,
):
    if (base_date is None) != (base_time is None):
        raise ValueError("base_date와 base_time은 함께 입력해야 합니다.")

    if base_date is None and base_time is None:
        base_date, base_time = get_latest_base_date_time()

    raw_data = await weather_client.fetch_weather_from_kma(base_date, base_time, nx, ny)

    try:
        response = raw_data["response"]
        header = response["header"]
        result_code = str(header["resultCode"])
        result_message = str(header["resultMsg"])
    except (KeyError, TypeError) as error:
        raise ValueError("기상청 API 응답 형식이 올바르지 않습니다.") from error

    if result_code != "00":
        raise ValueError(f"기상청 API 호출에 실패했습니다. 코드: {result_code}, 메시지: {result_message}")

    try:
        items_container = response["body"]["items"]
        items = items_container["item"]
    except (KeyError, TypeError) as error:
        raise ValueError("기상청 응답에서 예보 데이터를 찾을 수 없습니다.") from error

    if not items:
        raise ValueError("기상청에서 반환된 예보 데이터가 없습니다.")

    if isinstance(items, dict):
        items = [items]

    if not isinstance(items, list):
        raise ValueError("기상청 예보 데이터 형식이 올바르지 않습니다.")

    forecasts = parse_weather_items(items, nx=nx, ny=ny, base_date=base_date, base_time=base_time)

    if not forecasts:
        raise ValueError("TMP, POP, PTY가 모두 포함된 예보를 찾지 못했습니다.")

    saved_forecasts = weather_crud.save_weather_forecasts(db=db, forecasts=forecasts)
    return saved_forecasts


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None