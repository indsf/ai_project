# app/modules/recommend/service.py

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from app.modules.recommend import crud

# 추천 날씨 정규화 
from app.modules.recommend.weather_normalizer import (
    normalize_weather,
)
from app.modules.recommend import crud, weather_client


# 구미시 대표 기상청 격자 좌표
DEFAULT_NX = 84
DEFAULT_NY = 96

# 단기예보 발표 시각
BASE_TIMES = [
    2,
    5,
    8,
    11,
    14,
    17,
    20,
    23,
]

# 단기예보 PTY 코드
RAIN_TYPE_MAP = {
    "0": "NONE",
    "1": "RAIN",
    "2": "RAIN_SNOW",
    "3": "SNOW",
    "4": "SHOWER",
}

def get_current_weather_context(
    db: Session,
) -> dict:
    """
    현재 시각과 가장 가까운 날씨를 조회한 뒤
    추천에 사용할 날씨 정보로 변환한다.
    """

    now_kst = datetime.now(
        ZoneInfo("Asia/Seoul")
    ).replace(tzinfo=None)

    weather = crud.get_nearest_weather(
        db=db,
        target_at=now_kst,
    )

    if weather is None:
        raise ValueError(
            "현재 시각 이후의 예보가 없습니다."
        )

    normalized_weather = normalize_weather(
        temperature=weather.temperature,
        rain_type=weather.rain_type,
    )

    return {
        "weather_id": weather.id,
        "forecast_at": weather.forecast_at,
        "temperature": weather.temperature,
        "rain_prob": weather.rain_prob,
        "rain_type": weather.rain_type,
        "normalized_weather": normalized_weather,
    }


def get_latest_base_date_time(
    now: datetime | None = None,
) -> tuple[str, str]:
    """
    현재 시각을 기준으로 기상청에서 조회 가능한
    가장 최근 단기예보 발표 날짜와 시간을 계산한다.

    단기예보 발표 시각:
    02, 05, 08, 11, 14, 17, 20, 23시

    발표 직후 바로 제공되지 않을 수 있으므로
    발표시각 10분 이후를 조회 가능 시점으로 판단한다.
    """

    korea_timezone = ZoneInfo("Asia/Seoul")

    if now is None:
        current_time = datetime.now(korea_timezone)
    elif now.tzinfo is None:
        current_time = now.replace(tzinfo=korea_timezone)
    else:
        current_time = now.astimezone(korea_timezone)

    # 오늘 발표된 예보 중 현재 조회 가능한 가장 최근 시각 탐색
    for hour in reversed(BASE_TIMES):
        available_at = current_time.replace(
            hour=hour,
            minute=10,
            second=0,
            microsecond=0,
        )

        if current_time >= available_at:
            return (
                current_time.strftime("%Y%m%d"),
                f"{hour:02d}00",
            )

    # 오전 2시 10분 이전이면 전날 23시 예보 사용
    previous_day = current_time - timedelta(days=1)

    return (
        previous_day.strftime("%Y%m%d"),
        "2300",
    )


def parse_weather_items(
    items: list[dict[str, Any]],
    *,
    nx: int,
    ny: int,
    base_date: str,
    base_time: str,
) -> list[dict[str, Any]]:
    """
    기상청 단기예보 항목을 예보 날짜·시간별로 묶고
    DB에 저장할 데이터 구조로 변환한다.
    """

    grouped: dict[
        tuple[str, str],
        dict[str, Any],
    ] = defaultdict(dict)

    # 1. 같은 fcstDate + fcstTime별로 데이터 묶기
    for item in items:
        category = item.get("category")
        forecast_date = item.get("fcstDate")
        forecast_time = item.get("fcstTime")
        forecast_value = item.get("fcstValue")

        if category not in {"TMP", "POP", "PTY"}:
            continue

        if not forecast_date or not forecast_time:
            continue

        key = (
            str(forecast_date),
            str(forecast_time).zfill(4),
        )

        grouped[key][category] = forecast_value

    base_datetime = datetime.strptime(
        f"{base_date}{base_time}",
        "%Y%m%d%H%M",
    )

    forecasts: list[dict[str, Any]] = []

    # 2. 시간대별 데이터 생성
    for (
        forecast_date,
        forecast_time,
    ), values in sorted(grouped.items()):

        # TMP, POP, PTY가 모두 있는 시간대만 저장
        required_categories = {
            "TMP",
            "POP",
            "PTY",
        }

        if not required_categories.issubset(values):
            continue

        forecast_at = datetime.strptime(
            f"{forecast_date}{forecast_time}",
            "%Y%m%d%H%M",
        )

        temperature = to_float(values.get("TMP"))
        rain_prob = to_int(values.get("POP"))

        raw_rain_type = str(
            values.get("PTY", "0")
        )

        rain_type = RAIN_TYPE_MAP.get(
            raw_rain_type,
            "UNKNOWN",
        )

        forecasts.append(
            {
                "nx": nx,
                "ny": ny,
                "base_datetime": base_datetime,
                "forecast_at": forecast_at,
                "temperature": temperature,
                "rain_prob": rain_prob,
                "rain_type": rain_type,
            }
        )

    return forecasts


async def process_and_save_weather(
    db: Session,
    nx: int = DEFAULT_NX,
    ny: int = DEFAULT_NY,
    base_date: str | None = None,
    base_time: str | None = None,
):
    """
    날씨 데이터 처리 파이프라인

    1. 최신 단기예보 발표 시각 계산
    2. 기상청 API 호출
    3. API 응답 검증
    4. 시간대별 TMP·POP·PTY 전처리
    5. SQLite 저장
    """

    # 날짜와 시간 중 하나만 들어온 경우 차단
    if (base_date is None) != (base_time is None):
        raise ValueError(
            "base_date와 base_time은 함께 입력해야 합니다."
        )

    # 값을 직접 전달하지 않으면 현재 시각 기준으로 자동 계산
    if base_date is None and base_time is None:
        base_date, base_time = (
            get_latest_base_date_time()
        )

    # 1. 기상청 API 호출
    raw_data = await weather_client.fetch_weather_from_kma(
        base_date,
        base_time,
        nx,
        ny,
    )

    # 2. API 응답 헤더 검증
    try:
        response = raw_data["response"]
        header = response["header"]

        result_code = str(header["resultCode"])
        result_message = str(header["resultMsg"])

    except (KeyError, TypeError) as error:
        raise ValueError(
            "기상청 API 응답 형식이 올바르지 않습니다."
        ) from error

    if result_code != "00":
        raise ValueError(
            "기상청 API 호출에 실패했습니다. "
            f"코드: {result_code}, 메시지: {result_message}"
        )

    # 3. 예보 목록 꺼내기
    try:
        items_container = response["body"]["items"]
        items = items_container["item"]

    except (KeyError, TypeError) as error:
        raise ValueError(
            "기상청 응답에서 예보 데이터를 찾을 수 없습니다."
        ) from error

    if not items:
        raise ValueError(
            "기상청에서 반환된 예보 데이터가 없습니다."
        )

    # 항목이 하나일 경우 dict로 올 수도 있으므로 list로 통일
    if isinstance(items, dict):
        items = [items]

    if not isinstance(items, list):
        raise ValueError(
            "기상청 예보 데이터 형식이 올바르지 않습니다."
        )

    # 4. 시간대별 데이터 전처리
    forecasts = parse_weather_items(
        items,
        nx=nx,
        ny=ny,
        base_date=base_date,
        base_time=base_time,
    )

    if not forecasts:
        raise ValueError(
            "TMP, POP, PTY가 모두 포함된 예보를 "
            "찾지 못했습니다."
        )

    # 5. DB 저장
    saved_forecasts = crud.save_weather_forecasts(
        db=db,
        forecasts=forecasts,
    )

    return saved_forecasts


def to_int(value: Any) -> int | None:
    """
    기상청 문자열 값을 정수로 변환한다.
    변환할 수 없으면 None을 반환한다.
    """

    if value is None:
        return None

    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> float | None:
    """
    기상청 문자열 값을 실수로 변환한다.
    변환할 수 없으면 None을 반환한다.
    """

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------
# 단독 실행 테스트
# ---------------------------------------------------------
if __name__ == "__main__":
    import asyncio

    from app.core.database import (
        Base,
        SessionLocal,
        engine,
    )

    # 모델을 import해야 SQLAlchemy가 테이블을 인식한다.
    from app.modules.recommend import models

    Base.metadata.create_all(bind=engine)

    

    async def test():
        db = SessionLocal()
        


        try:
            print(
                "파이프라인 실행: "
                "기상청 호출 → 전처리 → DB 저장"
            )

            results = await process_and_save_weather(
                db=db,
            )

            print(
                f"DB 저장 완료: 총 {len(results)}건"
            )

            # 저장된 예보 중 앞의 5건만 출력
            for result in results[:5]:
                print(
                    "----------------------------"
                )
                print(f"ID: {result.id}")
                print(
                    f"예보 시각: {result.forecast_at}"
                )
                print(
                    f"기온: {result.temperature}℃"
                )
                print(
                    f"강수확률: {result.rain_prob}%"
                )
                print(
                    f"강수형태: {result.rain_type}"
                )
                weather_context = get_current_weather_context(db)
                print("현재 추천용 날씨")
                print(f"예보 시각: {weather_context['forecast_at']}")
                print(f"기온: {weather_context['temperature']}℃")
                print(f"강수확률: {weather_context['rain_prob']}%")
                print(f"강수형태: {weather_context['rain_type']}")
                print(
                    f"추천용 날씨: "
                    f"{weather_context['normalized_weather']}"
                )

        finally:
            db.close()

    asyncio.run(test())