# S1 선박 의약품 재고 관리 — Specification

## 목표 요약
- 선박별 의약품의 유효기한 기반 재고 관리(입고, FEFO 차감), 최소 비치 감지, 재고 조회 및 사용 이력 추적을 제공한다.
- 대상 기술 스택: Java/Kotlin, Spring Boot, PostgreSQL(설계 기준).

## 범위(요구사항 S1의 6개 기능)
- 약품 카탈로그 관리
- 선박별 최소 비치 기준 관리(단일 정책)
- 재고 입고(로트 단위)
- 약품 사용(출고) — FEFO(First-Expiry-First-Out)
- 재고 현황 조회(부족·유효기한 임박 포함)
- 사용 이력(누가 언제 어떤 로트에서 얼마를 사용했는지)

## 공통 운영 규칙
- 모든 시간과 날짜는 UTC로 저장·비교한다.
- 사용자 식별은 HTTP 헤더 `User-ID`로 전달되며, 시스템은 문자열 `user_id`로 보관한다.
- 모든 수량은 정수 단위(개수)로 취급한다.
- `receivedAt`(입고시각)을 생략하면 서버의 현재 UTC 시간이 적용된다.
- 만료(expiry_date < now(UTC)) 로트는 차감 대상에서 제외되며, 조회 시 `isExpired` 플래그로 표시한다.

## 데이터 모델(요약)
※ 아래는 구현 시 참고할 테이블·제약·인덱스 명세(DDL 수준의 구현 세부사항은 개발자가 적용).

- `drugs`
  - id (PK, UUID)
  - code (unique)
  - name, category, unit
  - created_at, updated_at

- `ships`
  - id (PK, UUID)
  - name, registry_no, ...

- `minimum_stock_policies`  (단일 정책으로 설계)
  - id (PK, UUID)
  - ship_id (FK -> ships.id)
  - drug_id (FK -> drugs.id)
  - minimum_quantity (int >= 0)
  - created_at, updated_at
  - 제약: UNIQUE(ship_id, drug_id) — 선박·약품별 단일 정책만 허용

- `batches` (입고 로트)
  - id (PK, UUID)
  - ship_id (FK), drug_id (FK)
  - batch_no (varchar) — 식별자, UNIQUE(ship_id, batch_no) 권장
  - quantity_total (int >= 0)
  - quantity_available (int >= 0)  -- DB CHECK 권고: CHECK (quantity_available >= 0)
  - expiry_date (timestamp)
  - received_at (timestamp)
  - created_at, updated_at
  - 인덱스: (ship_id, drug_id, expiry_date), (ship_id, batch_no)
  - 유도 상태:
    - `isExpired` := expiry_date < now(UTC)
    - `isClosed` := quantity_available == 0
  - 설명: `status` 컬럼은 제거(중복 상태이므로 유도) — 실무에서 상태 필요 시 decisions.md 참조

- `usage_records`
  - id (PK, UUID)
  - ship_id, drug_id
  - requested_quantity (int)
  - actual_quantity (int)
  - request_id (varchar, optional) — idempotency key
  - user_id (varchar)
  - status (enum: success, partial, failed)
  - created_at
  - 인덱스: UNIQUE(ship_id, request_id) — requestId 제공 시 중복 방지

- `usage_allocations`
  - id (PK, UUID)
  - usage_record_id (FK)
  - batch_id (FK)
  - allocated_quantity (int > 0)
  - before_batch_available (int) — 차감 전 가용량

## 인덱스·제약 요약
- `batches(ship_id, drug_id, expiry_date)` — FEFO 선택 최적화
- `batches(ship_id, batch_no)` — 로트 조회
- `usage_records(ship_id, request_id)` UNIQUE — idempotency
- DB 레벨 권장 CHECK: `batches.quantity_available >= 0`

## API 사양(요약, 변경사항 반영)
- 공통: 모든 요청은 `User-ID` 헤더 포함.

- POST /drugs
  - Request: { code, name, category, unit }
  - Response 201: { id, code, name, category, unit }

- GET /drugs/{id}
  - Response 200: { id, code, name, category, unit }

- POST /ships/{shipId}/minimum-stock
  - Request: { drugId, minimumQuantity }
  - Response 201: { id, shipId, drugId, minimumQuantity }
  - Note: `effectiveFrom` 제거; 시스템은 (ship_id, drug_id) 단일 정책만 관리

- GET /ships/{shipId}/minimum-stock
  - Response 200: [ { drugId, minimumQuantity } ... ]

- POST /ships/{shipId}/stock/inbound
  - Request: { drugId, batchNo, quantity, expiryDate, receivedAt(optional) }
  - Behavior: if receivedAt omitted -> server sets receivedAt = now(UTC)
  - Validation: quantity > 0, expiryDate parsable and >= receivedAt
  - Response 201: { batchId, shipId, drugId, batchNo, quantityTotal, quantityAvailable, expiryDate }

- POST /ships/{shipId}/stock/use
  - Request: { drugId, quantity, requestId(optional) }
  - Behavior summary:
    - FEFO allocation performed over non-expired batches with quantity_available > 0.
    - FEFO order: `expiry_date ASC, received_at ASC, id ASC` (deterministic).
    - If requestId provided: system enforces idempotency (UNIQUE(ship_id, request_id)).
    - Allocation outcomes:
      - Success (actualQuantity == requestedQuantity) → 201 Created
      - Partial (0 < actualQuantity < requestedQuantity) → 200 OK (status: 'partial')
      - Failure (actualQuantity == 0) → 422 Unprocessable Entity (status: 'failed')
    - Note: Partial success is only valid when actualQuantity >= 1. If no non-expired available stock exists (actualQuantity == 0), return 422.
    - If requestId provided and a prior usage_record exists:
      - If prior request payload (drugId, quantity) matches current request → return prior result (same HTTP code and body).
      - If prior request payload differs → return 409 Conflict.
  - Responses (examples):
    - 201: { usageRecordId, status: 'success', actualQuantity, allocations: [ { batchId, batchNo, allocatedQuantity, remainingBatchQuantity } ] }
    - 200: { usageRecordId, status: 'partial', actualQuantity, requestedQuantity, allocations, shortage }
    - 422: { error: 'no_available_stock', detail: 'no non-expired batches available' }
    - 409: { error: 'request_id_conflict' }

- GET /ships/{shipId}/stock
  - Query params: drugId(optional), includeExpired=false
  - Response 200: { drugId, totalAvailable, batches: [ { batchId, batchNo, availableQuantity, expiryDate, isExpired, receivedAt } ], minimumQuantity(optional), isBelowMinimum:boolean }
  - Note: `isBelowMinimum` indicates detection only; usage is not blocked.

- GET /ships/{shipId}/usage
  - Query params: drugId, from, to
  - Response 200: [ { usageRecord, allocations[] } ]

## 상태 코드 요약
- 201 Created: 사용 요청이 전량 성공 및 입고 생성 등
- 200 OK: 부분 성공(실제 차감량 >= 1이고 요청량보다 작음)
- 422 Unprocessable Entity: 실제 차감량이 0(만료 재고만 존재하거나 가용 재고 없음)
- 409 Conflict: requestId 충돌(동일 requestId, 다른 payload) 또는 동시성 충돌(락/낙관적 실패 등)
- 400/404/500: 기존과 동일

## 핵심 비즈니스 로직(의사코드, 변경 반영)

- 입고 처리
  - Validate input; if receivedAt omitted set receivedAt = now(UTC)
  - Insert `batches` row with quantity_total and quantity_available
  - (만료여부는 조회 시 유도 상태로 판단)

- 사용(출고) — FEFO
  - Begin transaction
  - If requestId provided:
    - Attempt to SELECT existing `usage_records` WHERE ship_id=:shipId AND request_id=:requestId FOR UPDATE
    - If exists:
      - If stored (drugId, requested_quantity) == incoming payload → return stored result (idempotent)
      - Else → return 409 Conflict
  - Select candidate batches:
    - SELECT * FROM batches
      WHERE ship_id = :shipId AND drug_id = :drugId AND expiry_date >= now(UTC) AND quantity_available > 0
      ORDER BY expiry_date ASC, received_at ASC, id ASC
      FOR UPDATE
  - Iterate candidate batches, allocate until requested quantity fulfilled or candidates exhausted.
  - For each allocation: atomically decrement `batches.quantity_available` (ensure DB constraint quantity_available >= 0) and insert `usage_allocations` recording before_batch_available.
  - Compute actualQuantity = sum(allocated)
  - If requestId provided → persist `usage_record` with status = success/partial/failed accordingly (failed when actualQuantity == 0)
  - If no requestId provided:
    - If actualQuantity == 0 → return 422 (no record persisted)
    - Else persist usage_record (success or partial)
  - Commit transaction
  - Return response per outcome

## 동시성 및 무결성 권고
- 사용 API는 단일 트랜잭션 내에서 candidate batch 행을 `FOR UPDATE`로 잠근 후 차감·기록을 수행하라.
- DB 레벨 CHECK(quantity_available >= 0)를 추가하고, 차감은 `UPDATE ... WHERE id = :id AND quantity_available >= :alloc` 패턴으로 원자성을 보장하라.
- requestId 기반 idempotency는 UNIQUE(ship_id, request_id)로 제약하고, 동시성은 INSERT-ON-CONFLICT/SELECT-FOR-UPDATE 패턴으로 처리하라(구현 예시는 decisions.md 참조).

## 오류 처리(요약)
- 입력 검증 오류 → 400
- 만료 재고만 존재(또는 실제 차감 0) → 422
- requestId 충돌(동일 requestId, 다른 payload) → 409
- 동시성 재시도 불가 → 409

## Edge Cases(변경 반영)
- 동일 expiry_date/received_at 동시성 tie-break: 추가 최종 tie-breaker `id ASC` 적용.
- 로트 상태는 `expiry_date`와 `quantity_available`로 유도함(별도 `status` 컬럼 제거).
- receivedAt 생략 시 서버시간 적용.
- 입고 수량 0 또는 음수: 400 Reject.
- 백데이팅: 허용하되 감사 필드로 기록.

## Given-When-Then 테스트(수정된 항목)
- TC-01 정상 FEFO: (변경없음)

- TC-02 만료 배제 (명확화)
  - Given: All batches for drug D on ship S have expiry_date < now
  - When: POST /ships/S/stock/use { quantity=1 }
  - Then: 422 Unprocessable Entity, no allocations created; if requestId provided, a `usage_record` with status='failed' is persisted for idempotency.

- TC-03 동시성 경쟁
  - Given: Single Batch X qty=10
  - When: Two concurrent POST use requests each quantity=8
  - Then: Total allocated must not exceed 10; one request may be success(8), other partial(2); verify no negative quantity_available and no double allocation.

- TC-04 부분 처리
  - Given: Total available 5
  - When: request 8
  - Then: status=partial, actual_quantity=5, shortage=3 (partial only when actual_quantity >=1)

- TC-05 idempotency
  - Given: Same requestId used twice with identical payload
  - When: repeat request
  - Then: second call returns prior record and allocations (same HTTP code/body), no additional deduction
  - Given: Same requestId used with different payload
  - When: POST
  - Then: 409 Conflict

- TC-06 최소비치·재고 조회
  - Given: minimum_stock_policies contains minimum_quantity for drug D on ship S
  - When: GET /ships/S/stock?drugId=D
  - Then: Response includes minimumQuantity and isBelowMinimum flag true if totalAvailable < minimumQuantity; this is detection only (usage not blocked)

---

