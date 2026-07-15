# app/modules/recommend/weather_client.py
# 실시간 기상청 api 호출을 담당하는 모듈 (외부 api 통신)

import httpx

from app.core.config import KMA_API_KEY


KMA_FORECAST_URL = (
    "https://apis.data.go.kr/"
    "1360000/VilageFcstInfoService_2.0/getVilageFcst"
)


async def fetch_weather_from_kma(
    base_date: str,
    base_time: str,
    nx: int,
    ny: int,
) -> dict:
    params = {
        "serviceKey": KMA_API_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    timeout = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(KMA_FORECAST_URL, params=params)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError as error:
            raise ValueError("기상청 응답을 JSON으로 변환하지 못했습니다.") from error