<p align="center">
  <img src="https://img.shields.io/badge/Version-0.3.0-brightgreen.svg" alt="Version">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-purple.svg" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/Skills-6-orange.svg" alt="6 Skills">
  <img src="https://img.shields.io/badge/Vault-Obsidian_호환-7c3aed.svg" alt="Obsidian Compatible">
  <a href="https://github.com/jhs512/ib/stargazers"><img src="https://img.shields.io/github/stars/jhs512/ib?style=social" alt="GitHub Stars"></a>
</p>

# Infinite Brain — AI 에이전트를 위한 영구적·타입 기반 기억

[English](README.md) | **한국어**

> AI 에이전트는 세션이 끝나면 모든 걸 잊습니다. **Infinite Brain**은 아무 폴더나 에이전트가 직접 만들고, 관리하고, 질의하는 타입 기반 지식그래프로 바꿔줍니다 — 모든 노트는 타입이 있는 **노드**, 모든 연결은 타입이 있는 **엣지**, 재검증 전까지 신뢰도가 감쇠하는 confidence 점수까지. Obsidian 호환, 순수 마크다운, DB 없음.

## 왜 노트 더미가 아니라 그래프인가?

길고 느슨하게 연결된 문서는 사람에겐 괜찮지만 에이전트에겐 망가진 구조입니다: 너무 많이 읽고, 링크는 두 노트가 *왜* 연결됐는지 말해주지 않고, 메타데이터는 신뢰할 만한 검색을 하기엔 너무 빈약합니다. Infinite Brain의 해법:

- **16+1 노드 타입** (`pillar`, `decision`, `fact`, `hypothesis`, `playbook`, …) — 노드당 아이디어 1개, 50–300 단어
- **10 엣지 타입** (`supports`, `contradicts`, `derived_from`, `depends_on`, …) — 모든 엣지에 방향·가중치·이유
- **신뢰 메타데이터** — `confidence`(0.0–1.0), `verified_at`, `staleness_signal`, `visibility`(`public`/`namespace`/`private`/`system`)
- **범위 제한 검색** — 볼트 전체(~9,000 토큰)가 아니라 엣지 탐색(~600 토큰)으로 답변
- **감사 추적** — 모든 스킬 실행이 경량 로그 노드를 남기고, 주간 헬스체크가 오래된 신뢰도를 자동 감쇠

## 스킬

| 명령 | 하는 일 |
|---|---|
| `/setup-ib` | 임의의 repo/폴더에 볼트 운영 컨텍스트 셋업 (최초 1회). 재실행 시 "싹 지우고 다시"(로컬) 옵션 |
| `/init-vault` | 완전한 볼트 스캐폴딩 — 폴더 17개, 시스템 스키마, 템플릿, 예시 노드 (보통 `/setup-ib`가 대신 호출) |
| `/convert-note` | `raw/`의 원자료를 원자적 타입 노드로 분해 |
| `/query-vault` | 그래프 탐색으로 질의응답 — 토큰 절약형 범위 검색 |
| `/organize-vault` | 대화형 감사: 고아 노드, 모순, 신뢰도 갭, 태그 난립 |
| `/vault-health` | 자동 유지보수: 신뢰도 감쇠 + 전체 감사 + 헬스 리포트 (`auto` 모드는 크론용) |
| `/setup-gcp` | *(선택, Sheets 미러용)* Google Cloud 자격증명을 계정당 1회 프로비저닝 — 프로젝트(기본 `infinite-brain`)·서비스계정·키, 멱등(있으면 재사용) |
| `/setup-sheets-sync` | *(선택, Sheets 미러용)* 현재 볼트를 Google Sheet(기본 `지식`)에 연동 — 시트 생성·공유·템플릿 복사·gh 연동·초기 동기화 |

## Google Sheets 미러 (선택)

Obsidian과 별개로, 볼트를 **Google 시트**로 미러링할 수 있습니다 — 지식그래프의 살아있는 **읽기 뷰**입니다. 마크다운이 항상 진실의 원천이고, 시트는 거기서 생성되는 투영본이라 필터·대시보드, 비개발자 공유, 또는 대화형 에이전트에 넘기기(예: Gemini 앱이 시트를 읽고 그래프 *위에서* 대화) 좋습니다.

```
마크다운 볼트(원천) ──push──▶ GitHub Action ──▶ sync.py ──▶ Google 시트(뷰)
  convert-note가 노드 저작        *.md 변경 시     해시 비교       _data · _edges
```

### 무엇을 동기화하나

그래프 탐색에 맞춰 두 탭으로 정규화:

| 탭 | 1행 단위 | 컬럼 |
|---|---|---|
| `_data` | 노드 | `id, title, type, namespace, visibility, summary, auto_inject, applicable_when, confidence, verified_at, verified_by, staleness_signal, tags, related, source_url, body` (+ 숨김 `_hash`) |
| `_edges` | 관계 | `source, type, target, weight, note` (+ 숨김 `_hash`) |

- `tags` / `related`는 셀 안 JSON이 아니라 **쉼표 구분 텍스트**.
- 관계는 각 노드의 `edges:` 프론트매터에서 자동 추출되어 `_edges`에 저장 → **양방향이 필터 한 번**: 나가는 = `source = X`, 백링크 = `target = X`.
- `_meta` 탭(있다면)은 사람·에이전트용 스키마 문서이며 sync가 건드리지 않음.

### 왜 싸고 정확한가

- **콘텐츠 해시 증분.** 노드/엣지 행을 정규화·해시하여 **바뀐 행만** 기록. 추가/삭제는 키 집합 비교(노드 키=`id`, 엣지 키=`source|type|target`).
- **캐시 파일 없음.** 기준 해시가 각 탭의 숨김 `_hash` 열에 있음(로컬 파일 ❌). GitHub Actions 러너는 매번 새 VM이라 로컬 캐시는 사라짐 — 상태를 *시트에* 두어 스테이트리스 CI에서도 정확하고, 시트가 손편집돼도 **자가 교정**.
- **작고 일정한 API 호출.** 탭당: **`id`+`_hash` 열만** 읽는 `batch_get` 1회(**body는 안 읽음** — 해시가 본문까지 담고 있음) + 변경분용 `batch_update`/`append_rows`/`deleteDimension`. 호출 수는 행 수와 무관하고, 읽기 페이로드도 거의 안 늘어남.
- **상한.** 시트는 그래프 DB가 아님 — Google Sheets는 셀 1,000만 개(≈노드 50만 행)가 한계. 그 이상은 실제 저장소로 이전(마크다운 볼트는 영향 없음).

### 셋업 (`/setup-gcp` 1회 → `/setup-sheets-sync` 볼트별)

무거운 Google Cloud 작업을 **계정당 1회**만 하고 모든 볼트가 재사용하도록 두 스킬로 나눕니다:

**`/setup-gcp` — 계정당 1회 (멱등):**

1. Google Cloud 프로젝트(기본 `infinite-brain`) 생성 **또는 재사용** + Sheets·Drive API 사용 설정. `gcloud` 우선, 없으면 브라우저. 기존 프로젝트/서비스계정/키가 있으면 재사용하며 **중복 프로젝트를 만들지 않습니다**.
2. 서비스 계정·JSON 키 생성(또는 재사용). `gcloud`면 키를 자동 생성, 브라우저면 **★ JSON 키 다운로드는 사람이 클릭**(자격증명). 결과는 `~/.config/ib/sheets-sync.env` 에 저장해 재사용.

**`/setup-sheets-sync` — 볼트마다:**

3. 새 스프레드시트 생성(기본 이름 `지식`, Google Drive 도구 사용) 또는 기존 것 지정.
4. **★ 스프레드시트를 서비스 계정 이메일과 편집자로 공유**(권한 변경은 본인만 가능; 안 하면 403).
5. 암호화된 `GOOGLE_SA_KEY` 시크릿 + `SPREADSHEET_ID` 변수 설정, `sync.py`·워크플로를 레포에 복사.
6. push → **Sheets Sync** 액션이 변경된 노드/엣지를 자동 반영.

> `gcloud` 가 없으면 `/setup-gcp` 가 콘솔 단계에서 브라우저 자동화(예: Claude in Chrome)로 폴백하며, 꺼져 있으면 수작업으로 끌고 가지 않고 "켜라"고 안내합니다.

### git에 보관하는 CSV 스냅샷

매 실행 시 `sheet/_data.csv` · `sheet/_edges.csv` 도 빌드합니다 — 시트 내용을 순수 텍스트로
diff·버전관리할 수 있는 스냅샷을 레포에 커밋(`sheet/_meta.csv` 는 손으로 관리하는 스키마 문서).
Action이 갱신된 스냅샷을 자동 커밋백합니다.

### 실행 모드

```bash
python sync.py --vault .                     # api 증분(기본) — 바뀐 행만
python sync.py --vault . --dry-run           # 계획만 미리보기, 쓰기 없음
python sync.py --vault . --method overwrite  # 각 탭 clear 후 전체 다시 쓰기
python sync.py --vault . --rebuild           # api 방식: 탭 비우고 재생성
```

템플릿·테스트·전체 근거: [`skills/ib/setup-sheets-sync/`](skills/ib/setup-sheets-sync/).

### 트러블슈팅

| 증상 | 원인 → 해결 |
|---|---|
| `403 PERMISSION_DENIED` | 시트가 서비스 계정과 공유 안 됨 → `client_email`을 **편집자**로 **공유**. |
| `SPREADSHEET_ID is required` | 레포 변수 `SPREADSHEET_ID` 설정(로컬은 환경변수). |
| 엉뚱한 탭에 쓰거나 덮어씀 | 탭은 **이름**(`_data`/`_edges`)으로 매칭하고 첫 탭으로 폴백하지 않음 — 이름을 유지하거나 `NODE_TAB`/`EDGE_TAB` 설정. |
| md를 고쳤는데 "변경 없음" | 그 파일이 노드가 아님(`id`+`type` 프론트매터 필요) 또는 제외 폴더(`_system`, `_templates`, `raw` …) 안에 있음. |
| 브라우저에서 행이 비어 보임 | 긴 `body` 때문에 행이 매우 높아진 것 — 데이터는 있음(스크롤/수식 입력줄 확인; `body` 열 줄바꿈을 끄면 깔끔). |
| 잘 되다가 인증 실패 | `GOOGLE_SA_KEY` 시크릿이 깨짐(전체 JSON이어야 함) 또는 키 폐기됨 → 키 회전(FAQ 참고). |
| 시트가 어긋남/손상 | `python sync.py --vault . --rebuild` 로 싹 비우고 마크다운 기준 재생성. |

### FAQ

- **시트를 직접 편집해도 되나요?** 아니요 — 생성된 뷰라 다음 sync 때 덮어쓰입니다(볼트에 없는 행은 삭제). 마크다운에서 저작하세요.
- **그럼 지식은 어디에 추가하나요?** 볼트에서 — 예: `raw/`에 자료를 넣고 `/convert-note` 실행.
- **공개 레포인데 서비스 계정 키가 안전한가요?** 네 — 암호화된 GitHub **시크릿**으로 저장되고 커밋되지 않음(`*.json`은 git-ignore). 키 파일은 본인 PC에만 있음.
- **키는 어떻게 회전하나요?** GCP에서 서비스 계정의 새 JSON 키를 만들고 `gh secret set GOOGLE_SA_KEY < new-key.json` 실행 후 옛 키 삭제.
- **에이전트는 시트를 어떻게 쓰나요?** `_data`(노드)와 `_edges`(관계)를 읽음 — `summary`로 스캔, 엣지로 탐색(`source=X`/`target=X`), `body`로 깊이 파기.

## 설치

### Claude Code 플러그인 (마켓플레이스)

```shell
/plugin marketplace add jhs512/ib
/plugin install infinite-brain@ib
```

### skills CLI (Claude Code · Codex · Cursor · OpenCode)

```bash
# 전부 설치
npx skills@latest add jhs512/ib --all

# 골라서 설치
npx skills@latest add jhs512/ib --skill init-vault --skill query-vault

# 특정 에이전트에만
npx skills@latest add jhs512/ib -a claude-code
```

## 퀵스타트

```
1.  /setup-ib          # 1회 — 기본값 설정, 운영 블록 작성, 볼트 스캐폴딩까지
                       # (/init-vault를 대신 실행)
2.  raw/에 아무거나 투하   (아티클, 회의록, 녹취록 — 파일명만 잘 지으면 끝)
3.  /convert-note      # raw 파일 → 엣지로 연결된 원자적 타입 노드
4.  /query-vault       # 질문하면 에이전트가 그래프를 탐색
5.  /schedule weekly /vault-health auto    # 선택: 스스로 관리되는 기억
```

언제든 같은 폴더를 Obsidian으로 열어보세요 — Graph View가 에이전트의 기억을 라이브 노드 맵으로 그려줍니다.

## 복붙 프롬프트

설치 후 Claude Code에 그대로 붙여넣어 보세요:

**개인 지식 베이스**
```
/setup-ib — 개인용 볼트를 만들고 싶어. 네임스페이스는 "personal"로 하고,
볼트 초기화 후 지금 raw/에 있는 것들을 전부 변환해줘.
```

**팀 의사결정 로그**
```
/query-vault — 우리가 왜 MongoDB 대신 PostgreSQL을 선택했지? 그 결정을
뒷받침하는 근거까지 추적하고, 모순되는 노드가 있으면 알려줘.
```

**리서치 수집**
```
방금 raw/에 논문 5편을 넣었어. 전부 /convert-note 돌리고, 새 노드들이
내가 기존에 믿고 있던 것과 모순되는 지점을 /organize-vault로 찾아줘.
```

**기억 위생 관리**
```
/vault-health — 90일 넘게 검증 안 된 것들 신뢰도를 감쇠시키고, 재확인하거나
삭제해야 할 상위 5개를 알려줘.
```

## 이웃 저장소와의 관계

| 저장소 | 무엇인가 | 관계 |
|---|---|---|
| [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain) | Infinite Brain 방법론의 원조 볼트 템플릿 | **업스트림 원조.** 본 저장소는 이 방법론을 설치형 플러그인으로 패키징: 시스템 템플릿을 동봉한 자급자족형 `init-vault`, 온보딩용 `setup-ib`, skills CLI를 통한 멀티 에이전트 배포. |
| [Obsidian](https://obsidian.md/) + Dataview / Web Clipper | 사람용 볼트 브라우저와 수집 도구 | **상호 보완.** 에이전트가 그래프를 쓰고, Obsidian이 그려줍니다. 락인 없음 — 전부 순수 마크다운. |
| Claude Code 세션 메모리 / CLAUDE.md | 프로젝트별 에이전트 지침 | **다른 층위.** CLAUDE.md는 에이전트가 *어떻게 행동할지*, Infinite Brain은 *무엇을 아는지* — 버전 관리·감사·질의가 가능한 형태로 저장. |

## 저장소 구조

```
skills/
└── ib/                  # Infinite Brain 스킬 그룹
    ├── setup-ib/            #   온보딩 + 에이전트 규칙 시드
    ├── init-vault/          #   스캐폴더 + 동봉된 시스템 템플릿
    ├── setup-gcp/           #   (선택) Sheets 미러용 재사용 Google Cloud 자격증명
    ├── setup-sheets-sync/   #   (선택) 볼트별 Sheets 미러 연동 + 동기화 템플릿/테스트
    ├── convert-note/        #   raw → 원자 노드
    ├── query-vault/         #   범위 제한 그래프 검색
    ├── organize-vault/      #   대화형 감사
    └── vault-health/        #   감쇠 + 감사 + 리포트 (크론 지원)
.claude-plugin/
    ├── plugin.json      # Claude Code 플러그인 매니페스트
    └── marketplace.json # 마켓플레이스 등록 정보
```

새 스킬 추가: `skills/<group>/<name>/SKILL.md`를 만들고 frontmatter에 `name`·`description`을 넣은 뒤, 새 그룹이라면 `.claude-plugin/plugin.json`에 등록합니다.

## 크레딧 & 라이선스

[JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain)의 Infinite Brain 방법론 기반이며, [AI Impact — How to Build an Infinite Brain with AI](https://www.youtube.com/watch?v=z02Y-1OvWSM)에서 영감을 받았습니다.

[MIT](LICENSE)
