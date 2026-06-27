---
name: init-vault
description: >
  현재 디렉토리에 새 Infinite Brain 볼트를 처음부터 스캐폴딩한다.
  모든 폴더, 시스템 파일, 템플릿, 예시 노드를 생성한다.
  /init-vault 로 호출.
allowed-tools: Read, Write, Glob
---

# Init Vault — 새 Infinite Brain 스캐폴딩

현재 디렉토리에 새 Infinite Brain 볼트를 처음부터 만든다.

이 스킬은 순수 스캐폴더다: 폴더 구조, `_system/` 파일, 템플릿, 예시 노드를 찍어낸다. ib 셋업의 진입점은 — 새 디렉토리든 기존 repo든 — `/setup-ib`이며, 디렉토리를 분류하고 볼트 위치를 정하고 기본값을 모은 뒤 그 단계 중 하나로 이 스킬을 호출한다.

## Steps

1. namespace를 결정한다. 이미 제공됐으면(예: `/setup-ib`에서 결정된 채 호출됨) 사용하고 재질문하지 않는다. 아니면 묻는다: "이 볼트는 어떤 namespace로 시작할까요? (예: 'personal', 'work', 'research')". **문서 언어는 한국어로 고정**이므로 묻지 않는다 — 사람이 읽는 모든 노드 콘텐츠(title, summary, body, edge note)는 한국어로 작성하고, 구조 어휘 — frontmatter 키, 노드/엣지 타입 이름, visibility 값, `id` 슬러그, namespace, tags, 폴더명 — 는 항상 정규 영어로 유지한다(`vault-agents-template.md`의 Document Language 섹션 참고).
2. 루트 폴더 생성 — 노드 타입당 하나(17개, 자동 작성 로그 노드용 `logs/` 포함) + `raw/`, `_system/`, `_templates/`:
   `pillars decisions concepts questions playbooks tasks events patterns hypotheses facts sources bookmarks notes contacts references custom logs raw _system _templates`
3. git이 추적하도록 각 빈 폴더에 `.gitkeep` 생성.
4. `_system/` 파일 생성. **기억으로 쓰지 말 것** — 이 스킬의 `templates/` 폴더에 동봉된 참조 템플릿을 복사한다(경로는 이 SKILL.md 기준 상대):
   - `INDEX.md` ← `templates/INDEX.md` — 마스터 노드 인덱스, 타입당 표 하나. 두 예시 행을 step 7의 실제 예시 노드 ID로 교체하고 *Last updated* 날짜를 갱신.
   - `NODE-TYPES.md` ← `templates/NODE-TYPES.md` — 17개 노드 타입 전체 정의(사용자 생성 가능 16개 + `log`)
   - `EDGE-TYPES.md` ← `templates/EDGE-TYPES.md` — 10개 엣지 타입 전체 정의
   - `FRONTMATTER-SCHEMA.md` ← `templates/FRONTMATTER-SCHEMA.md` — 전체 필드 참조, 축소된 8필드 로그 스키마 포함
   - `LOCAL-TYPES.md` ← `templates/LOCAL-TYPES.md` — 커스텀 타입 자리표시자
   - `WORKFLOWS.md` ← `templates/WORKFLOWS.md` — 각 스킬 실행 시점, 스케줄 권장(주간 `/vault-health auto`), GitHub Actions 예시
   - `AGENTS.md` — 에이전트 운영 규칙. setup-ib 스킬 폴더의 시드(`../setup-ib/vault-agents-template.md`)를 복사하고 `<namespace>`를 step 1의 답으로, `<language>`를 한국어로 치환.
   - `_prompts/` — 빈 폴더(스킬이 채운다)
5. `_templates/Template - Infinite Node.md`를 `templates/node-template.md`에서 생성.
6. 운영 블록: `/setup-ib`에서 호출됐으면 이 단계를 전부 건너뛴다 — 운영 블록은 setup-ib 소관이고 이미 썼다. 아니면, 볼트 루트에 `CLAUDE.md`도 `AGENTS.md`도 **둘 다 없을 때만**, 에이전트를 `_system/AGENTS.md`와 5개 스킬로 안내하는 `CLAUDE.md`를 생성한다 — setup-ib 시드(`../setup-ib/vault-claude-block.md`)를 본문으로 쓰고 step 1의 namespace를 채운다. 둘 중 하나라도 이미 있으면 그대로 두고, 사용자에게 `/setup-ib`를 실행하라고 알린다(`## Infinite Brain vault` 블록을 기존 파일에 올바르게 병합해준다).
7. 사용자가 고른 namespace로 예시 노드 2개를 생성한다. `templates/example-pillar.md`와 `templates/example-decision.md`를 변형(ID 변경, `namespace` 설정, 전체 frontmatter + 50–300단어 본문 형태 유지). 사람이 읽는 콘텐츠 — `title`, `summary`, 본문 산문, edge `note` — 는 한국어로 작성하고, `id` 슬러그·`type`·`visibility`·`namespace`·`tags`는 정규 영어로 유지:
   - `pillars/pillar-[namespace]-foundation.md`
   - `decisions/decision-[namespace]-first.md`
   - `supports` 엣지로 연결.
8. `_system/INDEX.md`를 두 예시 노드로 갱신.
9. 확인: "볼트 초기화 완료. 폴더 X개 생성, 예시 노드 2개 연결. Obsidian으로 열고 /convert-note로 콘텐츠 수집을 시작하세요."

---

`templates/` 아래 파일들은 [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain) (MIT)에서 변형했다.
