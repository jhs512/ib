---
name: convert-note
description: raw/의 원본 콘텐츠를 받아 타입이 지정된 프론트매터와 엣지를 가진 원자적 Infinite Brain 노드로 분해한다. 처리할 원본 자료가 있을 때 사용. /convert-note로 호출.
allowed-tools: Read, Write, Edit, Glob, Grep
---

# Convert Note — 원본을 원자 노드로 분해

`raw/` 폴더의 원본 콘텐츠를 Infinite Brain 지식그래프로 받아들인다.

## 단계

1. 질문: "`raw/`의 어떤 파일을 변환할까요? (전체 처리는 'all')"
   - 원본 파일은 사전 정리가 필요 없다 — 설명적인 파일명(예: `2026-05-15-karpathy-llm-wiki.md`)이면 충분하다. 태깅과 분류는 `raw/`가 아니라 여기서 일어난다.
2. 대상 파일을 Read로 스캔한다. 원본 파일은 불변으로 취급 — 수정하지 않는다.
3. 원자적 노드로 분해한다 — 노드당 하나의 개념, 각 50–300단어. 300단어를 절대 넘기지 않는다: 더 긴 노드는 범위 한정 검색을 무력화한다.
4. 각 노드마다:
   - 사용자가 생성할 수 있는 16개 콘텐츠 타입 중 정확히 하나로 분류: `pillar decision concept question playbook task event pattern hypothesis fact source bookmark note contact reference custom` (17번째 타입 `log`는 스킬이 자동으로 기록 — 여기서 직접 할당하지 않는다)
   - `type-descriptive-slug` 형식(kebab-case)의 고유 `id`를 부여
   - `_system/FRONTMATTER-SCHEMA.md`의 모든 프론트매터 필드를 채운다
   - 10개 엣지 타입으로 최소 하나의 다른 노드와 연결: `related_to depends_on derived_from contradicts supports part_of preceded_by followed_by authored_by tagged_with`
   - 타입에 맞는 폴더에 배치 — 타입 이름의 복수형(`pillar` → `pillars/<id>.md`, `concept` → `concepts/<id>.md`, …; 불규칙: `hypothesis` → `hypotheses/`)
5. 각 노드 파일을 작성한다.
6. **필수:** 새 노드의 행 — `id`, `summary`, 엣지 수 — 을 `| ID | Summary | Edges |` 표 열에 맞춰 `_system/INDEX.md`의 올바른 타입 섹션에 추가한다. 인덱스가 갱신되지 않으면 `/query-vault`의 범위 한정 검색이 실패하고 볼트가 깜깜해진다.
7. 처리한 원본 파일을 `raw/`에서 `raw/processed/`로 옮긴다 (예: `raw/article.md` → `raw/processed/article.md`).
8. `_system/FRONTMATTER-SCHEMA.md`의 log 스키마로 로그 노드를 `logs/log-convert-note-YYYYMMDD-HHmmss.md`에 작성한다:
   - `operation: convert-note`
   - `affected_nodes`: 생성한 모든 노드 ID 목록
   - `summary`: 한 문장 — 원본 파일명 + 노드 수
   - 본문(30–80단어): 무엇을 처리했는지, 어떤 노드를 만들었는지, 분해 과정에서 내린 주목할 만한 결정.
9. 확인: "`raw/filename`에서 X개 노드를 변환했습니다. 원본은 `raw/processed/`로 이동. 로그 작성 완료."

## 규칙

- 개념을 절대 병합하지 않는다 — 더 원자적인 노드 쪽으로 기운다.
- `summary`는 200자 미만의 1–2문장이어야 한다.
- `confidence`는 원본에서 나온 실제 확신도를 반영해야 한다.
- `visibility`는 명확히 달리 지시되지 않으면 `namespace`가 기본값이다.
- `staleness_signal`은 구체적으로 관찰 가능한 조건이어야 한다.
- `tags`: 노드당 2–8개, 소문자 kebab-case.
- `namespace`: 콘텐츠 도메인에서 추론한다.
- `type: raw` 노드를 만들지 않는다 — `raw/`는 인박스일 뿐이다.
- 작성 전 항상 `_system/INDEX.md`를 확인해 ID 중복을 피한다.
- `title`, `summary`, 본문 산문, 엣지 `note` 필드는 볼트의 문서 언어(`_system/AGENTS.md` → Document Language 참고)로 작성하고, `id` 슬러그, `type`, 엣지 타입 이름, `visibility`, `namespace`, `tags`는 표준 영어로 유지한다. 노트 내용은 원본 파일과 다른 언어일 수 있다 — 변환하라.
