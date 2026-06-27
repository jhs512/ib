---
name: setup-ib
description: 임의의 repo/폴더에 Infinite Brain 볼트 운영 컨텍스트를 셋업한다 — `CLAUDE.md`/`AGENTS.md`에 `## Infinite Brain vault` 블록(운영 규칙 + ib 스킬 표 + 노드/엣지 빠른 참조)을 쓰고 `_system/` 스캐폴딩이 존재하도록 보장해, ib 스킬들이 이 디렉토리가 지식그래프 볼트임을 알게 한다. 볼트가 진실의 원천이므로 기본적으로 버전 관리도 함께 셋업한다(먼저 물어본 뒤 `git init` + 선택적 GitHub repo). `init-vault`, `convert-note`, `query-vault`, `organize-vault`, `vault-health` 첫 사용 전 1회 실행 — 또는 그 스킬들이 볼트 컨텍스트(taxonomy, namespace, `_system/` 진입점)를 못 찾는 것 같을 때. 재실행 시 "싹 지우고 처음부터 다시"(로컬 전용) 옵션을 제공한다. 선택적 Google Sheets 미러는 나중에 언제든 붙일 수 있는 애드온 — `setup-gcp`(1회, 재사용 자격증명) → `setup-sheets-sync`(볼트별) 두 스킬로 분리돼 있다.
disable-model-invocation: true
---

# Setup Infinite Brain (ib) skills

**ib** 스킬들이 전제하는 볼트별 설정을 스캐폴딩한다:

- **운영 블록** — `CLAUDE.md`(또는 `AGENTS.md`)의 `## Infinite Brain vault` 섹션. 모든 에이전트가 이 디렉토리를 타입 있는 노드/타입 있는 엣지 지식그래프로 인식하고, 어떤 `/`-명령이 이를 다루는지 알게 한다.
- **`_system/` 진입점** — `AGENTS.md`(taxonomy, 가시성 모델, frontmatter 스키마, 금지 행동)와 `INDEX.md`(모든 새 노드가 갱신해야 하는 마스터 노드 인덱스).
- **기본값** — 시작 namespace와 기본 노드 visibility. (문서 언어는 한국어로 고정 — 선택 없음.)

이 스킬은 결정적 스크립트가 아니라 프롬프트 주도 스킬이다. 탐색하고, 찾은 것을 제시하고, 사용자와 확인한 뒤 쓴다. 참고: [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain).

이 스킬은 어떤 디렉토리(신규든 기존이든)에 ib를 셋업하는 진입점이다. `/init-vault`는 폴더 구조를 찍어내는 순수 스캐폴더로, 이 스킬이 위임 호출한다 — 셋업할 때 사용자를 `/init-vault`로 직접 안내하지 말 것.

**범위.** 이 스킬은 로컬 볼트 운영 컨텍스트만 셋업한다. 선택적 Google Sheets 미러는 이 스킬 *다음에* 실행하는 두 스킬로 분리돼 있다: **`/setup-gcp`**가 재사용 가능한 Google Cloud 자격증명을 1회 프로비저닝(멱등 — 기존 프로젝트/키 재사용)하고, **`/setup-sheets-sync`**가 이 볼트에 미러를 연결한다. 아래 step 6 참고.

## Process

### 0. 재실행이면: 깨끗한 리셋 제안

먼저 이 디렉토리에 이미 ib 컨텍스트가 있는지 확인한다(`CLAUDE.md`/`AGENTS.md`의 `## Infinite Brain vault` 블록, 또는 `_system/` 디렉토리). 있으면 사용자가 셋업을 재실행하는 것이다. 다음 중 무엇을 원하는지 묻는다:

- **제자리 업데이트**(기본) — 기존 내용을 유지하고 namespace/visibility 기본값만 조정하거나 빠진 부분만 보수. step 1로 계속.
- **싹 지우고 처음부터 다시** — 로컬 볼트 컨텍스트를 지우고 새로 빌드.

리셋을 고르면 파괴적이므로:

1. **삭제될 것을 정확히 나열**하고 무엇이든 건드리기 전에 명시적 확인을 받는다:
   - `CLAUDE.md`/`AGENTS.md`의 `## Infinite Brain vault` 블록(그 블록만 — 파일 나머지는 둔다),
   - `_system/`,
   - 노드 타입 폴더(`pillars/`, `decisions/`, `concepts/`, … `raw/`) — **ib가 만든 것이고 사용자가 확인할 때만**. 이전 스캐폴드로 귀속할 수 없는 폴더는 절대 지우지 말 것,
   - `_templates/Template - Infinite Node.md`.
2. **먼저 커밋 또는 stash를 강력히 권고**(`git status` / `git stash`)해 삭제가 복구 가능하게 한다. 디렉토리가 git repo가 아니면 삭제가 복구 불가임을 경고한다.
3. 확인된 대상을 지우고, step 1–5를 새 셋업으로 진행한다.

**리셋은 로컬 전용이다.** Google Sheet, GCP 프로젝트/서비스 계정, `gh` secret/variable은 절대 건드리지 않는다 — 그것들은 `/setup-gcp`와 `/setup-sheets-sync`로 관리(필요 시 철거)한다. 재동기화가 여전히 기존 시트에 동작해도 사용자가 놀라지 않도록 이 점을 명시한다.

### 1. 탐색

현재 디렉토리의 시작 상태를 파악한다. 존재하는 것은 읽고, 가정하지 말 것:

- 루트의 `CLAUDE.md`와 `AGENTS.md` — 둘 중 하나라도 있는가? 이미 `## Infinite Brain vault`(또는 `## Agent skills`) 섹션이 있는가?
- `_system/` — 존재하는가? 어떤 파일이 있는가(`AGENTS.md`, `INDEX.md`, `NODE-TYPES.md`, `EDGE-TYPES.md`, `FRONTMATTER-SCHEMA.md`)?
- 루트의 노드 타입 폴더(`pillars/`, `decisions/`, `concepts/`, … `raw/`) — 이미 스캐폴드된 볼트인가, 부분적인가, 평범한 repo인가?
- `_templates/Template - Infinite Node.md` — 볼트 템플릿이 만들어졌는가?
- `git remote -v` — 볼트도 원하는 코드 repo인가, 전용 볼트 디렉토리인가?

디렉토리를 다음 중 하나로 분류한다: **(a) 이미 완전한 볼트**, **(b) 부분적**(`_system/` 또는 폴더 일부), **(c) 아직 볼트 아님**.

### 2. 결과 제시 후 질문

무엇이 있고 무엇이 빠졌는지 요약한다. 그다음 결정들을 **하나씩** 사용자와 진행한다 — 한 섹션 제시, 답 받기, 다음으로. 한꺼번에 쏟아붓지 말 것.

사용자가 이 용어들을 모를 수 있다고 가정한다. 각 섹션은 짧은 설명(무엇인지, ib 스킬이 왜 필요로 하는지, 다른 선택 시 무엇이 바뀌는지)으로 시작한 뒤 선택지와 기본값을 제시한다.

**Section A — 볼트 위치 & 스캐폴딩.**

> 설명: ib 스킬은 `pillars/`, `decisions/`, `concepts/` 같은 폴더와 taxonomy·마스터 인덱스를 담는 `_system/` 디렉토리 아래 타입 있는 노드를 읽고 쓴다. 볼트 *그 자체*인 장소가 필요하다. 전용 볼트 디렉토리면 그게 루트고, 기존 코드 repo면 보통 루트에 17개 노드 폴더를 두고 싶지 않으므로 볼트를 하위 폴더에 둔다.

- **루트** — 이 디렉토리가 볼트. 전용 볼트 repo에 적합. (`src/`, `package.json` 등이 없으면 기본값.)
- **하위 폴더**(예: `vault/` 또는 `brain/`) — 기존 프로젝트의 하위 폴더에 볼트. 폴더 이름을 묻는다.

그다음 step 1의 분류에 따라:
- **아직 볼트 아님** 또는 **부분적**이면, 선택한 위치에서 `/init-vault`를 실행해 전체 구조(17개 폴더, `_system/` 파일, 템플릿, 예시 노드 2개)를 스캐폴딩할지 제안한다. 사용자가 거절하면 최소만 시드: `_system/AGENTS.md`와 `_system/INDEX.md`.
- **이미 완전**하면 스캐폴딩을 건너뛴다 — CLAUDE.md 블록과 기본값만 쓰면 된다.

**Section B — Namespace.**

> 설명: 모든 노드는 상위 영역으로 묶는 `namespace`(예: `personal`, `work`, `research`)를 가진다. 볼트는 여러 namespace를 담을 수 있지만, 지정하지 않을 때 새 노드에 찍을 기본값이 필요하다.

기본값: `personal`. 사용자에게 시작 namespace를 묻는다.

**Section C — 기본 visibility.**

> 설명: 모든 노드는 `visibility`를 가진다 — `public`(namespace 간·일반 답변에 안전), `namespace`(노드의 namespace와 작업이 맞을 때만 사용), `private`(사람이 그 비공개 컨텍스트를 명시적으로 요청할 때만 사용), `system`(에이전트용 운영 규칙, 사용자 콘텐츠로 절대 제시 안 함). 스킬은 이 기본값을 새 노드에 적용한다.

기본값: `public`(볼트가 여러 영역을 섞을 거면 `namespace` 사용 — 불확실하면 upstream은 `namespace` 권장). 확인하거나 덮어쓴다.

**Section D — 버전 관리(git). 항상 묻고, 기본은 yes.**

> 설명: 볼트는 *진실의 원천*이므로 버전 관리 아래 있어야 한다 — git은 히스토리·diff·복구를 준다(step 0의 리셋이 안전한 건 git이 복구할 수 있어서다). 또한 나중의 선택적 Google Sheets 미러의 하드 요구사항이다(동기화가 GitHub Action으로 돈다). git 없는 볼트는 정상이 아니라 예외다.

이건 기본 단계이지 부가가 아니다 — **조용히 건너뛰지 말 것.** `git rev-parse --is-inside-work-tree`와 `git remote -v`를 확인한다:

- **git repo 아님** → 초기화할지 묻는다(기본 **yes**). 동의하면 repo 루트에서 `git init`. 명시적 거절 없이는 "버전 관리 없는" 볼트로 진행하지 말 것.
- **GitHub remote 없음** → 지금 만들지 묻는다(기본 **yes** — Sheets 미러가 필요로 하고 미리 해두면 싸다). yes이고 `gh`가 인증돼 있으면 `gh repo create <name> --private --source=. --remote=origin`(이름과 private/public을 사용자와 확인). **`gh`가 설치돼 있지 않으면 먼저 설치를 안내한다** — <https://cli.github.com/>(Windows: `winget install GitHub.cli`, macOS: `brew install gh`), 그다음 `gh auth login`(세션에서 바로 보려면 `! gh auth login`). 사용자가 설치를 원치 않으면 나중에 remote 추가하는 법을 알려준다.
- **이미 remote 있는 git repo** → 할 일 없음. 기록하고 넘어간다.

repo가 git 기반인지, GitHub remote가 있는지 기록한다 — step 6이 Sheets 미러 전에 무엇이 필요한지 사용자에게 알릴 때 쓴다.

### 3. 확인 후 편집

사용자에게 다음 초안을 보여준다:

- step 4에서 편집할 `CLAUDE.md` / `AGENTS.md`에 추가할 `## Infinite Brain vault` 블록 — `<namespace>`, `<visibility>`가 채워진 상태. (문서 언어는 한국어 고정.)
- 생성될 `_system/` 파일 목록(있다면), 또는 "이미 존재 — 그대로 둠".
- Section D의 버전 관리 동작(예: "`git init` + private GitHub repo `<name>` 생성", 또는 "이미 git 기반 — 할 일 없음").

쓰기 전에 편집하게 한다.

### 4. 쓰기

**편집할 파일 선택:**

- `CLAUDE.md`가 있으면 그것을 편집.
- 없고 `AGENTS.md`가 있으면 그것을 편집.
- 둘 다 없으면 어느 것을 만들지 사용자에게 묻는다 — 대신 고르지 말 것.

`CLAUDE.md`가 이미 있으면 `AGENTS.md`를 만들지 말 것(반대도). 항상 이미 있는 것을 편집한다. 선택한 파일에 `## Infinite Brain vault` 블록이 이미 있으면 중복 추가 대신 그 내용을 제자리에서 갱신한다. 주변 섹션의 사용자 편집을 덮어쓰지 말 것.

이 스킬 폴더의 시드 — [vault-claude-block.md](./vault-claude-block.md) — 를 출발점으로 블록을 쓰되, Section B/C의 namespace·visibility를 치환한다(문서 언어는 한국어 고정). 볼트가 하위 폴더에 있으면 블록 첫 줄에 경로를 적는다("The `vault/` directory is an AI-first knowledge-graph vault…").

그다음 `_system/` 진입점이 존재하도록 한다:

- 사용자가 `/init-vault`를 선택했으면, 선택한 위치에서 호출하고 Section B의 namespace를 넘겨(문서 언어는 한국어 고정) 재질문하지 않게 하며, 그 스킬의 운영-블록 단계는 건너뛴다 — CLAUDE.md/AGENTS.md 블록은 이 스킬의 일이고 위에서 막 썼다.
- 아니면 다른 ib 스킬이 읽을 최소를 시드: `_system/AGENTS.md`와 `_system/INDEX.md`(타입별 빈 표). `AGENTS.md`는 이 스킬 폴더의 시드 — [vault-agents-template.md](./vault-agents-template.md) — 를 복사하고 Section B의 `<namespace>`를 치환한다(문서 언어 한국어). 이 시드는 전체 운영 규칙(taxonomy, 가시성 모델, frontmatter 스키마, 문서 언어 규칙, 로그 작성 규칙, 금지 행동, 첫 세션 프로토콜)을 담는다. 기존 `_system/` 파일은 건드리지 말 것.

그다음 **Section D**의 버전 관리 결정을 수행한다: 사용자가 동의했고 아직 repo가 아니면 `git init`; 선택했으면 `gh`로 GitHub repo 생성. 방금 repo를 초기화했다면 스캐폴드된 볼트를 첫 커밋한다(이후로 step 0의 리셋이 복구 가능하도록).

### 5. 완료 (코어 셋업)

볼트 컨텍스트가 설정됐고 어떤 ib 스킬이 이제 필요한 것을 갖췄는지(`init-vault`, `convert-note`, `query-vault`, `organize-vault`, `vault-health`) 알리고, 버전 관리 상태(git repo, GitHub remote — 또는 아직 필요한 것)를 확인해준다. `## Infinite Brain vault` 블록이나 `_system/*.md`는 나중에 직접 편집할 수 있고 — 이 스킬 재실행은 namespace/visibility 기본값 변경, 볼트 이전, 깨끗한 리셋(step 0)에만 필요함을 언급한다.

### 6. 선택: Google Sheets 미러 — 지금 또는 나중에 언제든

> 설명: 선택적으로 볼트를 Google Sheet로 미러링한다 — 그래프 탐색에 맞게 정규화된 표 형태 **읽기 뷰**로, `_data` 탭(노드당 1행)과 `_edges` 탭(관계당 1행). 마크다운이 진실의 원천으로 남고, GitHub Action이 push마다 **변경된 노드/엣지만** 재동기화한다. 필터·집계·대시보드, 비기술 사용자와의 공유에 유용.

이건 **기본 off**이며 완전히 **나중에 붙일 수 있는 애드온**이다: 지금 거절해도 코어 셋업은 아무것도 바뀌지 않고, 아래 두 스킬을 돌려 **나중에 언제든** 켤 수 있다 — `/setup-ib` 재실행 불필요. 건너뛰는 게 일회성 문이 아님을 사용자에게 명시한다. 계정 단위의 무거운 자격증명 작업이 1회만 일어나 모든 볼트에서 재사용되도록 두 스킬로 분리돼 있다:

1. **`/setup-gcp`** — Google Cloud 프로젝트 + 서비스 계정 + JSON 키를 **1회** 프로비저닝. 멱등: 기존 `infinite-brain` 프로젝트와 키를 중복 생성 대신 재사용한다. 이후 볼트에서는 건너뛴다 — 저장된 자격증명(`~/.config/ib/sheets-sync.env`)을 재사용.
2. **`/setup-sheets-sync`** — *이* 볼트에 미러를 연결: 기본으로 `지식` 이름의 Google Sheet 생성, 서비스 계정과 공유, 동기화 템플릿 복사, `gh` secret/variable 설정, 초기 동기화. GitHub repo가 필요한데 — Section D가 기본으로 셋업하므로 나중에 그냥 동작한다.

지금이든 나중이든, `/setup-gcp`를 먼저 안내한다(또는 자격증명이 없으면 `/setup-gcp`를 안내하는 `/setup-sheets-sync`).
