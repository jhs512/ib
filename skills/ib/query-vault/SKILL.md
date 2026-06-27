---
name: query-vault
description: 타입이 지정된 엣지와 가시성 필터로 지식그래프를 탐색해 질문에 답한다. 선택적으로 순회해 토큰 비용을 약 9000에서 약 600으로 줄인다. /query-vault로 호출.
allowed-tools: Read, Write, Glob, Grep
---

# Query Vault — 범위 한정 그래프 검색

Infinite Brain 지식그래프를 탐색해 질문에 답한다.

## 단계

1. 질문: "무엇을 알고 싶으신가요?"
2. `_system/INDEX.md`를 Read한다 — 기존 노드의 전체 지도를 얻는다.
3. 범위를 정한다:
   - 네임스페이스가 명시됨 → 해당 네임스페이스의 노드를 우선한다
   - 네임스페이스 없음 → `public` 노드를 사용하고, `namespace` 노드는 summary가 명확히 일치할 때만 사용한다
   - 명시적 private 요청 → `private` 노드를 사용한다
   - `system` 노드를 답변 내용으로 제시하지 않는다
4. 질문 형태에 따라 가능성 높은 노드 타입을 선택한다:
   - "왜" → `pillar`, `decision`
   - "어떻게" → `playbook`, `pattern`
   - "만약 ~라면" → `hypothesis`
   - "무엇" → `concept`, `fact`
   - "언제/어디서" → `event`, `note`
   - "누구" → `contact`
   - 미해결 의문 → `question`
5. 엣지로 탐색한다 — 모든 노드를 읽지 않는다:
   - `supports` / `contradicts` → 대립하는 입장을 찾는다
   - `derived_from` → 결론을 근거까지 추적한다
   - `depends_on` → 선행 조건을 찾는다
6. `summary`, `applicable_when`, `namespace`, `visibility`가 일치하는 노드만 읽는다.
7. 다음 형식으로 종합해 출력한다. 답변 산문, 출처 설명, 저장할 종합 노드는 볼트의 문서 언어(`_system/AGENTS.md` → Document Language 참고)로 작성하고, `[[node-id]]` 참조, 타입 이름, 기타 구조 어휘는 표준 영어로 유지한다:

---

### 답변
<직접적인 답변, 1–3문단>

### 출처
- `[[node-id]]` — <기여한 내용>

### 신뢰도
<출처 노드들의 confidence 값 평균, 0.0–1.0>

### 탐색해 볼 관련 노드
- `[[node-id]]` — <관련 이유>

---

질문: "이것을 종합 노드로 저장할까요?"

8. `_system/FRONTMATTER-SCHEMA.md`의 log 스키마로 로그 노드를 `logs/log-query-vault-YYYYMMDD-HHmmss.md`에 작성한다:
   - `operation: query-vault`
   - `affected_nodes`: 순회 중 읽은 노드 ID
   - `summary`: 한 문장 — 던진 질문(필요시 100자로 절단)
   - 본문(30–80단어): 던진 질문, 순회한 노드, 반환한 신뢰도, 종합 노드 저장 여부.
