---
name: vault-health
description: 볼트 유지보수 워크플로 - 신뢰도 감쇠 + 전체 헬스 감사 + 리포트 노드. 두 가지 모드 - interactive(/vault-health)는 수정 전에 묻고, automated(/vault-health auto)는 리포트만 작성하고 신뢰도를 감쇠한다(수정 없음, 질문 없음).
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Vault Health — 유지보수 워크플로

## 모드 판별

**첫 번째 인자를 확인한다:**
- 인자 없음 → **interactive 모드**: 모든 단계를 실행하고, 수정 실행 전에 묻는다.
- 인자가 `auto` → **auto 모드**: 1~3단계만 실행하고 4단계 전에 멈춘다. 질문 없음. 수정 없음. 리포트를 작성하고 종료한다.

auto 모드는 사람이 없는 예약 실행을 위해 설계되었다.

---

## Phase 1 — 신뢰도 감쇠

두 모드 모두에서 안전하게 실행할 수 있다. 감쇠는 결정론적이며 git으로 되돌릴 수 있다.

1. `_system/INDEX.md`를 읽어 전체 노드 목록을 파악한다.
2. 각 노드에 대해 프론트매터를 읽고 `verified_at` 이후 경과 일수를 계산한다.
3. 감쇠를 적용한다:

| 검증 후 경과 일수 | 동작 |
|---|---|
| 91–180 | `confidence`를 0.1 감소(하한: 0.1) |
| 181–365 | `confidence`를 0.2 감소(하한: 0.1) |
| > 365 | `confidence`를 0.1로 설정, tags에 `needs-review` 추가 |
| > 90 AND staleness_signal 발동 | `confidence`를 0.1로 설정 |

4. `confidence` 필드만 갱신한다(>365 경우에는 `tags`도). 그 외에는 아무것도 건드리지 않는다.
5. 추적 항목: 스캔한 노드 수, 감쇠한 노드 수, 타입별 분류.

**건너뜀:** `visibility: system` 노드, `verified_at: "Empty"` 노드, 생성된 지 30일 미만인 노드.

---

## Phase 2 — 헬스 감사

발견 사항만 수집한다. 이 단계에서는 어떤 노드도 수정하지 않는다.

1. **고아 노드 조사** — 엣지 0개 AND `related` 링크 0개.
2. **모순 스캔** — 같은 네임스페이스 내 충돌하는 주장.
3. **신뢰도 누락** — `confidence`가 없거나 0.0이거나, staleness 신호가 발동된 노드에 높은 신뢰도.
4. **낡은 노드** — `verified_at` > 90일. 우선순위: pillars > decisions > facts > patterns > hypotheses.
5. **교차 링크 기회** — 태그를 2개 이상 공유하면서 엣지가 없는 노드.
6. **분류체계 건강도** — 일관성 없는 태그 표기, 거의 중복인 태그.
7. **가시성 건강도** — `visibility` 누락 또는 내용 민감도와 충돌하는 가시성.
8. **요약 품질** — 200자 초과, 플레이스홀더 텍스트, 내용 불일치 요약.

---

## Phase 3 — 헬스 리포트 노드 작성

두 모드 모두에서 실행한다. auto 모드에서는 (감쇠 외에) 유일한 쓰기 작업이다.

리포트의 사람이 읽는 텍스트 — `title`, `summary`, 이슈 설명, 제안 수정안 — 은 볼트의 문서 언어로 작성한다(`_system/AGENTS.md` → Document Language 참고). 프론트매터 키, `id`, `type`, `visibility`, `namespace`, 태그, 파일 경로는 표준 영어로 유지한다.

`notes/note-vault-health-YYYYMMDD.md`를 생성한다:

```yaml
---
id: note-vault-health-YYYYMMDD
title: "Vault Health Report — YYYY-MM-DD"
type: note
namespace: system
visibility: system
summary: "Automated health report: X nodes audited, Y decayed, Z issues found."
auto_inject: false
applicable_when: "Empty"
confidence: 1.0
verified_at: "MM/DD/YYYY"
verified_by: "vault-health-workflow"
staleness_signal: "Superseded by a newer health report node"
tags: ["vault-health", "automated", "maintenance"]
edges: []
related: []
source_url: "Empty"
---

## Vault Health — YYYY-MM-DD

### Mode
auto | interactive

### Decay Summary
- Nodes scanned: XX
- Nodes decayed: XX
- By type: concept: X, decision: X, fact: X, ...

### Audit Summary
- Total nodes: XX
- Orphans: XX | Contradictions: XX | Stale: XX | Cross-link opportunities: XX

### Priority Actions
1. [ ] [high] ...
2. [ ] [med]  ...

### Details
| File | Issue | Suggested fix |
|---|---|---|
```

`_system/INDEX.md`를 새 노트로 갱신한다.

---

## Phase 4 — 대화형 수정 루프

**auto 모드: 이 단계를 완전히 건너뛴다. Phase 3 이후 종료한다.**

interactive 모드 전용:

Priority Actions 목록을 출력하고 묻는다:

"헬스 리포트를 `notes/note-vault-health-YYYYMMDD.md`에 작성했습니다. 어떤 작업을 실행할까요? (번호로 답하거나 'none')"

사용자가 선택한 것만 실행한다. 각 수정에 대해: 변경을 확인하고, 적용하고, 리포트 노드에서 해당 작업을 `[x]`로 표시한다.
