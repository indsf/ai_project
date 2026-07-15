# ai project

## 축제 + 커뮤니티 파트

`app/modules/posts` (커뮤니티 게시판)과 `app/modules/places` (관광지/레포츠/문화시설/쇼핑/숙박/
여행코스/음식점/축제공연행사 통합) 두 모듈이 있습니다.

`festival` 모듈은 `places`로 흡수 통합됐습니다. **`/api/festivals`는 이제 없고 `/api/places/festivals`
를 씁니다** — 프론트에서 예전 경로로 호출하는 코드가 있으면 고쳐야 합니다.

## 실행

```bash
python -m venv venv
venv\Scripts\activate   # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

`http://127.0.0.1:8000/docs` 에서 Swagger로 바로 테스트 가능합니다. 서버 기동 시 `app/data/`
안의 8개 카테고리 JSON이 전부 자동으로 시딩됩니다(태그도 이때 자동 계산).

## 왜 테이블을 하나로 합쳤는가

TourAPI 8개 카테고리(관광지/레포츠/문화시설/쇼핑/숙박/여행코스/음식점/축제공연행사) 파일은
필드 구조가 완전히 동일합니다(SCHEMA.md 참고). `contentTypeId`만 다르고 나머지는 같아서,
카테고리마다 테이블/모델/crud/service/router를 8번 복붙하는 대신 **테이블 하나(`places`) +
`content_type_id` 구분 컬럼**으로 통합했습니다. 대신 엔드포인트는 통합검색용 하나 + 카테고리
전용 8개로 나눠서, 프론트 입장에서는 카테고리별로 깔끔하게 호출할 수 있게 했습니다.

```
app/modules/places/
├── categories.py   # contentTypeId <-> URL슬러그 <-> 파일명 매핑 (여기 한 줄 추가하면 카테고리 추가됨)
├── models.py       # Place 모델 (테이블 하나, category는 content_type_id에서 파생되는 property)
├── schemas.py
├── crud.py
├── service.py       # 시딩 파이프라인 + 거리 정렬 + recommend 모듈에 노출할 공개 인터페이스
└── router.py        # 통합검색 1개 + 카테고리 전용 8개 + 상세조회 1개 + 시딩 1개
```

## API

### 커뮤니티 (`/api/posts`)
| Method | Path | 설명 |
|---|---|---|
| GET | `/api/posts?category=&search=&page=&size=` | 목록 |
| GET | `/api/posts/{id}` | 상세 (조회수 +1) |
| POST | `/api/posts` | 작성 |
| PUT | `/api/posts/{id}` | 수정 (비밀번호 필요) |
| DELETE | `/api/posts/{id}?password=` | 삭제 |

### 장소 통합검색 (`/api/places`)
| Method | Path | 설명 |
|---|---|---|
| GET | `/api/places?search=&category=&tags=&match=&lat=&lng=&page=&size=` | 통합 검색 (전체 8개 카테고리) |
| GET | `/api/places/{content_id}` | 단건 상세 (카테고리 무관) |
| POST | `/api/places/seed` | 8개 카테고리 전체 재시딩 (서버 기동 시 자동 실행됨) |

`category` 파라미터는 쉼표로 여러 개 넘길 수 있습니다: `category=festivals,restaurants`

### 카테고리 전용 엔드포인트 (통합검색과 로직 동일, 카테고리만 고정)
| Path | 카테고리 |
|---|---|
| `GET /api/places/attractions` | 관광지 |
| `GET /api/places/culture` | 문화시설 |
| `GET /api/places/festivals` | 축제공연행사 |
| `GET /api/places/courses` | 여행코스 |
| `GET /api/places/leisure` | 레포츠 |
| `GET /api/places/lodging` | 숙박 |
| `GET /api/places/shopping` | 쇼핑 |
| `GET /api/places/restaurants` | 음식점 |

각 엔드포인트는 `search`, `tags`, `match`, `lat`, `lng`, `page`, `size`를 통합검색과 동일하게 받습니다.
예: `GET /api/places/festivals?tags=rain&lat=36.13&lng=128.33`

## 날씨 태그

`app/core/weather_tags.py`에 규칙 기반 MVP 태거가 있습니다. TourAPI 원본에는 실내/실외 여부가
없어서, **제목 키워드 매칭 → 안 맞으면 contentTypeId 기본값**으로 추론합니다. 8개 카테고리 전부
같은 로직으로 시딩 시점에 자동 태깅됩니다(수동 작업 불필요).

태그 어휘: `indoor`, `outdoor`, `rain`, `hot`, `cold`, `sunny`, `any_weather`
(rain/hot/cold는 대부분 indoor에 자동으로 같이 붙습니다 — "실내니까 비/더위/추위 상관없이 갈만함")

카테고리별 대략적인 분포(총 1667건):

| 카테고리 | outdoor | indoor | 비고 |
|---|---|---|---|
| 관광지 | 484 | 15 | 자연/유적 위주라 야외가 압도적 |
| 레포츠 | 107 | 3 | 캠핑/승마/골프 등 야외 위주 |
| 문화시설 | 3 | 109 | 박물관/미술관/공연장 등 실내 위주 |
| 쇼핑 | 142 | 269 | 전통시장은 outdoor, 마트/브랜드매장은 indoor |
| 숙박 | 0 | 80 | 전부 indoor + any_weather |
| 여행코스 | 30 | 1 | 도보 코스라 야외 위주 |
| 음식점 | 1 | 393 | 거의 다 indoor |
| 축제공연행사 | 30 | 0 | 이 데이터셋엔 실내 행사가 안 잡힘 |

제목 키워드 기반이라 100% 정확하진 않습니다(브랜드명이 키워드 목록에 없으면 카테고리 기본값으로
잘못 분류될 수 있음). MVP로 빠르게 "대략 맞는" 태그를 까는 게 목적이고, 필요하면
`app/core/weather_tags.py`의 키워드 리스트를 보강하거나 개별 항목을 수동으로 고치면 됩니다.

## recommend 모듈에서 쓰는 법

```python
from app.modules.places.service import get_places_for_recommendation

# 비 오는 날 갈만한 축제/음식점 추천, 가까운 순
places = get_places_for_recommendation(
    db,
    categories=["festivals", "restaurants"],
    tags=["rain"],
    lat=36.13, lng=128.33,
    limit=10,
)
```

`places.crud`나 `places.models`를 recommend 모듈에서 직접 import하지 말고, 이 함수(공개
인터페이스)만 통해서 접근해야 합니다 (guide.md의 모듈 경계 규칙).

## 카테고리 추가하는 법

새 TourAPI 카테고리가 생기면:
1. `app/data/`에 원본 JSON 파일 넣기
2. `app/modules/places/categories.py`의 `CONTENT_TYPE_REGISTRY`에 한 줄 추가
3. 서버 재시작 (또는 `POST /api/places/seed` 호출)

그러면 통합검색과 `/api/places/{새슬러그}` 전용 엔드포인트가 자동으로 생깁니다.

## DB 마이그레이션 주의

기존에 `app.db` 파일이 있다면(이전 `festivals` 테이블 스키마) 지우고 다시 실행하세요.
SQLAlchemy `create_all`은 새 테이블(`places`)만 만들고 기존 테이블 구조를 바꾸진 않습니다.
`festivals` 테이블은 이제 안 쓰이니 그냥 `app.db`를 삭제하고 새로 시작하는 게 제일 깔끔합니다.

## 데이터 출처

`app/data/` 안 JSON은 한국관광공사 Tour API(TourAPI 4.0) 데이터이며 공공누리 제3유형
(출처표시+변경금지)입니다. tags 필드(DB 컬럼)는 원본이 아니라 우리가 추가한 파생 데이터라
원본 JSON 필드 값 자체는 건드리지 않았습니다. 프론트에 노출할 땐 아래 문구를 표기해야 합니다.

```
이 서비스는 한국관광공사 Tour API(TourAPI 4.0)의 데이터를 활용하였습니다.
출처: 한국관광공사 (https://www.data.go.kr/data/15101578/openapi.do)
```
