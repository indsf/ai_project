# app/modules/recommend/weather_client.py

# 실시간 기상청 api 호출을 담당하는 모듈 (외부 api 통신)


import asyncio
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
    """
    기상청 단기예보 API를 호출하고
    원본 JSON 데이터를 반환한다.
    """

    params = {
        # 일반 인증키의 Decoding 값을 사용한다.
        "serviceKey": KMA_API_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    timeout = httpx.Timeout(
        connect=5.0,
        read=15.0,
        write=5.0,
        pool=5.0,
    )

    async with httpx.AsyncClient(
        timeout=timeout,
    ) as client:
        response = await client.get(
            KMA_FORECAST_URL,
            params=params,
        )

        response.raise_for_status()

        try:
            return response.json()
        except ValueError as error:
            raise ValueError(
                "기상청 응답을 JSON으로 변환하지 못했습니다."
            ) from error


# ---------------------------------------------------------
# 단독 실행 테스트
# ---------------------------------------------------------
if __name__ == "__main__":

    async def test_run():
        print("기상청 서버로 요청을 보냅니다.")

        try:
            result = await fetch_weather_from_kma(
                base_date="20260714",
                base_time="2000",
                nx=84,
                ny=96,
            )

            header = (
                result
                .get("response", {})
                .get("header", {})
            )

            print(f"응답 상태: {header}")

            items = (
                result
                .get("response", {})
                .get("body", {})
                .get("items", {})
                .get("item", [])
            )

            if items:
                print(
                    "첫 번째 데이터:",
                    items[0],
                )
            else:
                print("예보 데이터가 없습니다.")
                print(result)

        except httpx.HTTPStatusError as error:
            print(
                "기상청 HTTP 오류:",
                error.response.status_code,
            )

        except httpx.RequestError as error:
            print(
                "기상청 연결 오류:",
                str(error),
            )

        except Exception as error:
            print(
                "처리 오류:",
                str(error),
            )

    asyncio.run(test_run())