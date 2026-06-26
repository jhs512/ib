# ib — Infinite Brain skills

Obsidian 기반 AI 지식그래프 볼트("Infinite Brain")를 운영하기 위한 스킬 그룹입니다.
모든 노트를 타입이 있는 **노드**로, 모든 연결을 타입이 있는 **엣지**로 다룹니다.

| 스킬 | 슬래시 명령 | 용도 |
|---|---|---|
| `setup-ib` | `/setup-ib` | 임의의 폴더/repo에 볼트 운영 컨텍스트(CLAUDE.md 블록 + `_system/`)를 셋업 — ib 스킬 첫 사용 전 1회 실행 |
| `init-vault` | `/init-vault` | 새 디렉토리에 볼트 전체 구조를 스캐폴딩 (보통 `/setup-ib`가 대신 호출) |
| `convert-note` | `/convert-note` | `raw/` 자료를 타입이 있는 원자적 노드로 분해 |
| `query-vault` | `/query-vault` | 그래프 탐색으로 질문에 답변 (토큰 절약형) |
| `organize-vault` | `/organize-vault` | 고아 노드·모순·신뢰도 갭 등 대화형 감사 |
| `vault-health` | `/vault-health` | 신뢰도 감쇠 + 전체 감사 + 헬스 리포트 노드 자동 생성 |

## 함께 쓰면 좋은 도구 (선택)

스킬은 Claude Code 기본 도구(Read/Write/Edit/Glob/Grep)만으로 동작합니다. 아래는 사람이 볼트를 탐색·운영하는 데 도움이 되는 보완 도구입니다(에이전트 동작에는 영향 없음):

- **Obsidian Graph View** — 볼트를 Obsidian으로 열면 `[[wikilink]]`·`related` 기반 노드 그래프를 즉시 시각화. 고아 노드·밀집 클러스터를 한눈에 파악.
- **Obsidian Web Clipper** — 웹 글을 `raw/`에 마크다운으로 바로 저장(`raw/YYYY-MM-DD-제목.md`). `/convert-note` 변경 불필요.
- **Dataview** — frontmatter를 쿼리해 라이브 대시보드 구성(예: `confidence < 0.5`인 노드 전부). `_system/DASHBOARD.md`에 쿼리를 두면 상시 헬스 뷰가 됨.
- **qmd(로컬 시맨틱 검색)** — 볼트가 ~200 노드를 넘으면 `/query-vault`의 1차 검색 단계로 BM25+벡터 하이브리드 검색을 보완 가능.
- **주간 자동화** — `/vault-health auto`를 주 1회 스케줄(`/schedule weekly /vault-health auto`) 또는 GitHub Actions cron으로 실행. 설정 예시는 init-vault가 생성하는 `_system/WORKFLOWS.md` 참고.
- **Google Sheets 미러** — `/setup-ib`가 선택적으로 볼트를 구글 시트로 단방향 동기화(노드 `_data` + 관계 `_edges` 탭, push 시 변경분만). 필터·대시보드·공유, 대화형 에이전트 그라운딩용. 템플릿: [`setup-ib/sheets-sync/`](./setup-ib/sheets-sync/).

원본 출처: [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain) (MIT)
