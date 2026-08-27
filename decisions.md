# Design Decisions — S1 선박 의약품 재고 관리

이 문서는 `docs/task.md`, `docs/analysis.md`, `docs/plan.md`와 검토자 코멘트를 바탕으로 주요 설계 선택과 그 근거를 정리한다. 리뷰어의 지적별로 반영 여부와 이유를 명시했다.

## 요약된 최종 선택
- 최소 비치 정책: **선박 단위 단일 정책**(UNIQUE(ship_id, drug_id), `effective_from` 제거)
- FEFO 우선순위: **expiry_date ASC, received_at ASC, id ASC** (결정론적 tie-break)
- 만료 재고: 보존하되 차감 대상에서 제외; **만료만 존재하면 사용 요청은 422 실패**(actualQuantity == 0)
- 부분처리: **허용하되** 실제 차감량이 1 이상일 때만 부분 성공으로 인정
- 동시성: 초기 전략은 **비관적 락(SELECT...FOR UPDATE)**, DB 무결성(체크 제약)과 재시도/백오프 정책 병행
- Idempotency: `requestId` 사용 시 **UNIQUE(ship_id, request_id)** 제약, 동일 요청 반복 시 기존 결과 반환, 동일 requestId 다른 payload → 409
- `batches.status` 컬럼: 제거(유도 가능한 상태는 계산으로 처리)

---

## 각 검토 지적에 대한 반영 여부 및 이유

1) 최소 비치 정책: `effective_from` 제거, (ship_id, drug_id) UNIQUE 유지
- 반영: 예
- 이유: 과제 요구(선박별 최소비치 관리)는 단일 active 정책만으로 요구를 충족한다. 시계열 정책을 도입하면 스펙·DB·조회 로직이 복잡해지고 과제 범위를 벗어난다. 향후 필요 시 decisions에 확장 방안을 제시.

2) `batches.quantity_available`에 CHECK (quantity_available >= 0) 추가
- 반영: 예
- 이유: 음수 재고는 절대 허용되지 않아야 하며 DB 차원 제약으로 데이터 정합성을 보장하는 것이 안전하다. 또한 애플리케이션 레벨의 원자적 UPDATE 패턴(`WHERE quantity_available >= :alloc`)과 병행해 음수 방지를 보장한다.

3) 만료 재고만 존재하여 실제 차감 수량이 0이면 422로 실패, 부분 사용은 actual >= 1일 때만 허용
- 반영: 예(통일 적용)
- 이유: 클라이언트에게 `0` 차감(무의미한 partial) 대신 명확한 실패(422)를 전달하는 것이 UX/운영상 명확하다. 이 규칙은 응급 상황에서의 혼선 방지에 도움이 된다.
- 구현 세부: requestId가 제공된 경우에는 실패 결과도 `usage_records`에 상태='failed'로 기록하여 idempotency가 보장되도록 한다. requestId 미제공 시에는 실패(422)를 반환하고 레코드 미생성(모니터링 필요 시 별도 로깅)을 권장한다.

4) FEFO 정렬을 `expiry_date ASC, received_at ASC, id ASC`로 확정
- 반영: 예
- 이유: 동일 expiry/received_at 경우에도 결정론적 처리를 위해 고유 식별자(id)를 최종 tie-breaker로 사용한다.

5) 최소 비치 기준은 사용 차단 기준이 아니라 부족 감지(알림) 정책으로 결정
- 반영: 예
- 이유: 과제 요구와 운영 시나리오(응급 사용)를 고려하면, 최소비치로 사용을 차단하면 위험이 있다. 대신 조회 응답에 `isBelowMinimum` 플래그를 제공하여 운영자가 조치할 수 있도록 한다.

6) `requestId` 관련 규칙(UNIQUE 제약 및 중복 처리 규정)
- 반영: 예
- 이유: 재시도/중복 요청으로 인한 중복 차감을 예방하려면 `requestId` 기반의 중복 방지 로직이 필요하다. 아래 동작 규칙을 문서화한다:
  - DB 제약: UNIQUE(ship_id, request_id)
  - 동작(요약):
    1. 요청에 `requestId`가 있으면 트랜잭션 시작 후 `usage_records`에서 (ship_id, request_id) 조회(FOR UPDATE).
    2. 존재하면 저장된 요청의 payload(drugId, requested_quantity)를 비교.
       - 동일하면 기존 결과를 그대로 반환(동일 HTTP 코드/바디).
       - 다르면 409 Conflict 반환(요청 불일치).
    3. 존재하지 않으면 빈 레코드(또는 pending 상태)를 삽입하고 allocation을 수행한 뒤 최종 상태(success/partial/failed)로 업데이트(동시성 race 방지).
  - 응답 코드: 최초 성공 → 201, 최초 partial → 200, 최초 실패(actual==0) → 422. 동일 요청 재전송은 기존 결과 반환.

7) `receivedAt` 생략 시 서버시간 적용
- 반영: 예
- 이유: 클라이언트 편의성 및 데이터 일관성을 위해 서버측 UTC now를 기본으로 사용한다. API 스펙에 명시함.

8) `batches.status` 제거(유도 상태로 전환)
- 반영: 예
- 이유: `status`(active/expired/closed)가 `expiry_date`와 `quantity_available`로 유도 가능하여 중복·불일치 소지가 있다. 상태는 유도하여 조회 시 계산된 값을 제공한다. 만약 운영상 명시적 상태 전이가 필요하면 별도 기능으로 추가하되, 이번 과제 범위에서는 제거한다.

---

## 동시성·무결성 관련 보완(권고)
- Deadlock 위험 완화: candidate batch 조회 시 일관된 정렬(order by id)로 잠금 순서를 고정하고, deadlock 발생 시 재시도(backoff) 전략을 문서화한다.
- 원자적 차감: `UPDATE batches SET quantity_available = quantity_available - :n WHERE id = :id AND quantity_available >= :n RETURNING ...` 패턴 권장.
- Idempotency race: `INSERT ... ON CONFLICT DO NOTHING RETURNING` 또는 트랜잭션 내 placeholder insert 후 조회 방식으로 동시성 경쟁 해결을 권고.

## 향후 확장(간단)
- 시계열 최소비치가 필요하면 `minimum_stock_policies`에 `effective_from/to` 필드와 시간범위 모델을 추가하고, 조회 시 유효한 정책을 선택하도록 설계 변경.
- 만료 자동 폐기/알림 기능은 배치 작업으로 분리해 이벤트 발행 또는 알림 채널 연동을 권장.

---

작성자(결정 기록): 시스템 설계팀
