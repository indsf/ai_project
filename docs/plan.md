목표: `spec.md`와 `decisions.md`를 작성하기 전에 설계·작성 범위와 기준을 정리한다. 아래 계획은 두 문서를 작성할 때 필요한 항목들(데이터 모델, API, FEFO 정책, 트랜잭션/동시성, 오류 처리, 테스트 시나리오)과 각 문서에 반영할 결정 범위를 명시한다.

**전제 및 방식**:
- **기술 스택:** Java/Kotlin, Spring Boot, PostgreSQL(명시된 제약 준수).
- **산출물 순서:** 본 파일(`docs/plan.md`) 작성 → 리뷰 → `spec.md` 작성 → `decisions.md` 작성.
- **결정 기록:** 모호한 항목은 `decisions.md`에 대안과 선택 근거를 반드시 기록.

**1. 데이터 모델 설계 항목**
- **핵심 엔티티:** `Drug`(카탈로그), `Ship`(선박), `MinimumStockPolicy`(선박별 최소비치), `Batch`/`StockLot`(입고 로트), `StockEntry`(실제 재고 행), `UsageRecord`(사용 트랜잭션), `UsageAllocation`(사용 시 어떤 로트에서 얼마를 차감했는지 매핑), `User`(기록용 식별자, 외래키 대신 문자열 `user_id` 허용).
- **주요 속성/제약:** 이름, SKU, 단위(unit), 로트번호(unique 범위 규칙), quantity(비음수), expiry_date(UTC 날짜/타임스탬프), received_at(입고 시각 UTC), ship_id(FK), minimum_quantity(정수/단위 표준화 규칙).
- **정합성 제약:** quantity >= 0, expiry_date 타입과 비교 기준(UTC 기준, 날짜 단위로 판단 여부 결정 필요).
- **인덱스:** (ship_id, drug_id), (ship_id, drug_id, expiry_date), (batch_no, ship_id) — 조회·FEFO·로트 조회 성능 최적화.

**2. API 설계 항목**
- **카탈로그:** POST `/drugs`, GET `/drugs/{id}`, GET `/drugs`(필터).
- **최소비치:** POST/PUT/GET `/ships/{shipId}/minimum-stock`(약품별 최소 수량 관리).
- **입고:** POST `/ships/{shipId}/stock/inbound` 요청 바디: `drugId, batchNo, quantity, expiryDate, receivedAt(optional)` 응답: 입고 레코드.
- **사용(출고) 요청:** POST `/ships/{shipId}/stock/use` 요청 바디: `drugId, quantity, requestId(optional for idempotency)` 응답: 사용 결과(성공/부분처리/실패) 및 `UsageAllocation` 목록(로트별 차감 내역).
- **재고 조회:** GET `/ships/{shipId}/stock?drugId=&includeExpired=` 응답: 현재 재고 요약 및 로트별 상세(유효수량, expiryDate).
- **사용 이력 조회:** GET `/ships/{shipId}/usage?drugId=&from=&to=` 응답: `UsageRecord` + `UsageAllocation` 상세.
- **상태 코드 및 에러:** 200/201(성공), 400(잘못된 입력), 404(자원 없음), 409(경합/동시성 충돌), 422(비즈니스 규칙 위반: 만료재고 사용 시도 등), 500(서버 오류).

**3. FEFO 차감 정책**
- **정의:** 요청 수량은 `expiry_date` 오름차순(가장 빠른 것부터)으로 차감한다.
- **동일 expiry tie-breaker:** 기본: `received_at` 오름차순(입고 순). 대안: 로트 번호 순 — 선택은 `decisions.md`에 기록.
- **만료 정책:** `expiry_date < now(UTC)`인 로트는 차감 대상에서 제외(시스템상 사용 불가). 만료 임박(예: 30일 이내)은 별도 플래그로 표시.
- **부분처리 규칙:** 요청 전체를 채울 수 없을 때 두 가지 옵션: (A) 전체 거부(원자성), (B) 가능한만큼 차감하고 부분 성공으로 응답. 기본은 (B)로 설계안 초안 작성하되, 최종 정책은 `decisions.md`에서 확정.
- **응답 데이터:** `UsageAllocation[]` — 각 항목은 `batchId, batchNo, allocatedQuantity, remainingBatchQuantity` 포함.

**4. 트랜잭션과 동시성 처리**
- **트랜잭션 범위:** 사용(출고) API는 단일 DB 트랜잭션 내에서 로트 선택 → 검증(만료/가용량) → 차감 → 사용 이력·할당 기록을 모두 수행.
- **잠금 전략(대응안들):**
  - **비관적 락:** `SELECT ... FOR UPDATE`로 관련 `StockEntry`(또는 `Batch`) 행을 잠그고 차감 — 구현 단순, 경쟁 높을 때 블로킹 위험.
  - **낙관적 락:** `version` 필드 사용(UPDATE ... WHERE version = ?)으로 재시도 로직 적용 — 높은 동시성에서 성능 우수하나 재시도 로직 필요.
  - **직렬화 수준 트랜잭션(Serializable):** 정확도는 높으나 성능 저하 우려.
- **권장 초안:** 우선 `SELECT ... FOR UPDATE`(행 단위)로 명확한 원자성 보장. 성능 문제 발견 시 낙관적 락 전환을 `decisions.md`에 기록.
- **Idempotency 및 중복 요청:** 클라이언트 제공 `requestId`로 `UsageRecord` 중복 기록 방지(사용 요청 재시도 시 중복 차감 방지). `requestId`는 unique index로 관리.

**5. 오류 처리**
- **입력 검증(400):** 필수 필드 누락, 수량 음수, 잘못된 날짜 포맷 등.
- **비즈니스 오류(422):** 만료 재고 사용 시도, 단위 불일치, 최소비치 규칙 위반(경고 또는 차감 허용 여부는 결정 필요).
- **동시성 충돌(409):** 잠금으로 인한 충돌이나 낙관적 락 실패시 409 반환 및 클라이언트에게 재시도 권장.
- **부분처리 알림:** 부분 처리 시 200 + `partial=true` + 상세 사유 및 남은 부족량 반환.
- **감사 및 로깅:** 모든 입고/사용 API는 `User-ID` 헤더를 로그·이력에 포함.

**6. Given-When-Then 테스트 시나리오(우선순위별 샘플)**
- 시나리오 1(정상 FEFO): Given 유효한 두 로트(A:exp=2026-09-01 qty=10, B:exp=2026-12-01 qty=10)가 있을 때, When 사용 요청 qty=12 실행하면 Then A에서 10, B에서 2 차감되고 UsageAllocation이 반환된다.
- 시나리오 2(만료 배제): Given 모든 로트가 만료되었을 때, When 사용 요청이 들어오면 Then 422 또는 부분 실패(선택에 따름) 응답.
- 시나리오 3(동시성): Given 재고 qty=10인 단일 로트에 대해 두 클라이언트가 동시에 qty=8 요청을 보낼 때, When 동시 처리하면 Then 하나는 성공(8), 다른 하나는 실패 또는 부분 성공(2) — 트랜잭션/락 동작 검증.
- 시나리오 4(부분처리 허용): Given 재고 총합 5, 요청 8이면 Then 부분 성공으로 5 차감, 남은 3은 부족으로 응답.
- 시나리오 5(idempotency): Given 동일한 `requestId`로 중복 요청이 재전송될 때 Then 두 번째 요청은 기존 결과를 반환하고 재차감하지 않음.

**7. `spec.md`와 `decisions.md`의 수정 범위(초안 계획)**
- `spec.md`에 포함할 내용(범위):
  - 데이터 모델 ERD 및 테이블별 DDL(컬럼, 제약, 인덱스)
  - API 엔드포인트별 요청/응답 스키마 및 상태 코드
  - 핵심 비즈니스 로직의 의사코드(입고, FEFO 차감 알고리즘, 부분처리 흐름)
  - 트랜잭션 경계와 예시 쿼리(잠금 사용 예시 포함)
  - Edge Case 목록 및 각 케이스 처리 방식
  - Given-When-Then 테스트 케이스(우선순위별)
- `decisions.md`에 포함할 내용(범위):
  - 각 모호 항목에 대한 후보안 나열 및 장단점(예: FEFO tie-breaker, 부분처리 허용 여부, 락 전략 등)
  - 최종 선택과 선택 이유(성능·정합성·운영 편의성 근거)
  - 향후 개선 제안(예: 이벤트화, 배치 자동 폐기, 모니터링 알람)

다음 단계: 이 계획을 리뷰 받으면 `spec.md` 작성(데이터 모델·API·의사코드 포함)으로 진행하겠습니다.
