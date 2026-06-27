---
name: organize-vault
description: 주기적 볼트 유지보수 - 고아 노드, 모순, 신뢰도 누락, 낡은 노드, 교차 링크 기회, 분류체계 건강도, 요약 품질을 감사한다. 주 1회 또는 격주로 실행한다. /organize-vault로 호출한다.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Organize Vault — 주기적 유지보수

Infinite Brain 지식그래프의 건강 이슈를 감사한다.

## 단계

1. `_system/INDEX.md`를 읽어 현재 상태 기준선을 파악한다.
2. 아래 8가지 검사를 실행한다.
3. 리포트를 전달한다.
4. "이 중 어떤 작업을 실행할까요?"라고 묻는다 — 확인 없이 자동 수정하지 않는다.

## 검사

**1. 고아 노드 조사**
엣지가 0개이고 `related` 링크도 0개인 노드를 찾는다. 각각에 대해 엣지 타입과 함께 연결 대상 2~3개를 제안한다. 진짜 독립 노드라면 `#standalone`으로 표시한다.

**2. 모순 스캔**
같은 네임스페이스 내 노드들을 비교해 충돌하는 주장을 찾는다. `hypothesis`/`fact`/`decision` 노드 간 모순되는 엣지에 특히 주의한다. `[node-a] contradicts [node-b] about [topic]` 형식으로 보고한다.

**3. 신뢰도 누락**
`confidence`가 없거나 0.0이거나 내용과 일치하지 않는 노드를 찾는다. 가용한 근거를 바탕으로 갱신할 값을 제안한다. 신뢰도는 높지만 staleness 신호가 발동된 노드를 표시한다.

**4. 낡은 노드 탐지**
`staleness_signal` 조건을 확인한다. `verified_at`이 90일 이상 지난 노드를 표시한다. 우선순위: pillars > decisions > facts > patterns > hypotheses.

**5. 교차 링크 기회**
태그를 2개 이상 공유하면서 엣지가 없는 노드를 찾는다. 근거와 함께 구체적인 엣지 타입과 가중치를 제안한다. 암묵적 계층 구조를 살핀다(patterns가 pillars를 구현, decisions가 hypotheses에서 파생 등).

**6. 분류체계 건강도**
마스터 태그 목록을 작성한다(없으면 새로 만든다). 일관성 없는 표기를 표시한다(예: "AI" vs "ai" vs "artificial-intelligence"). 거의 동일한 태그는 병합을 제안한다.

**7. 가시성 건강도**
`visibility`가 없는 노드를 찾는다. 내용 민감도나 네임스페이스 범위와 현재 설정이 충돌하면 표시한다. 항상 `public`, `namespace`, `private`, `system` 중 하나를 제안한다.

**8. 요약 품질**
200자 초과 또는 3문장 이상인 요약, 비어 있거나 플레이스홀더 텍스트("TBD", "description", "1-2 sentences..."), 노드 내용과 맞지 않는 요약을 표시한다.

## 출력 형식

리포트의 산문 — 이슈 설명, 제안 수정안, 작업 텍스트 — 은 볼트의 문서 언어로 작성한다(`_system/AGENTS.md` → Document Language 참고). 파일 경로, `id` 슬러그, type/edge/visibility 이름, 태그는 표준 영어로 유지한다.

```
## Vault Health — [Date]

### Summary
- Total nodes: XX | Orphans: XX | Contradictions: XX | Stale: XX | Cross-link opportunities: XX

### Priority Actions (Top 5)
1. [ ] [high] ...
2. [ ] [med]  ...
...

### Details
[File path | Issue | Suggested fix]
```

## 실행 후

리포트를 전달하고 사용자가 선택한 수정을 적용한 뒤:

`_system/FRONTMATTER-SCHEMA.md`의 로그 스키마를 사용해 `logs/log-organize-vault-YYYYMMDD-HHmmss.md`에 로그 노드를 작성한다:
- `operation: organize-vault`
- `affected_nodes`: 수정된 노드 ID(사용자가 "none"을 선택하면 빈 배열)
- `summary`: 한 문장 — 노드 수, 이슈 수, 적용된 수정 수
- 본문(30~80단어): 감사한 전체 노드 수, 검사별 발견된 이슈 수, 사용자가 승인하고 적용한 수정 수.
