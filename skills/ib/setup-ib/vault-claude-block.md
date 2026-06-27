<!--
setup-ib가 CLAUDE.md(또는 AGENTS.md)에 쓰는 `## Infinite Brain vault` 블록의 시드 템플릿.
<namespace>, <visibility>를 사용자의 답으로 치환한다. 문서 언어는 한국어로 고정(치환 없음).
블록이 이미 있으면 내용을 제자리에서 갱신 — 중복 추가 금지.
-->

## Infinite Brain vault

이 디렉토리는 AI-우선 지식그래프 볼트다. 모든 노트는 타입 있는 **노드**, 모든 연결은 타입 있는 **엣지**다. 채팅 어시스턴트가 아니라 Knowledge Architect로서 행동하라.

볼트 작업 전 반드시 `_system/AGENTS.md`를 읽어라 — 전체 노드/엣지 taxonomy, 가시성 모델, frontmatter 스키마, 금지 행동을 정의한다.

### ib skills

| Command | 사용 시점 |
|---|---|
| `/init-vault` | 새 디렉토리에 볼트 스캐폴딩 |
| `/convert-note` | `raw/` 파일을 타입 있는 원자적 노드로 분해 |
| `/query-vault` | 범위 한정 그래프 탐색으로 질문에 답변(토큰 절약형) |
| `/organize-vault` | 고아 노드·모순·신뢰도 갭 대화형 감사 |
| `/vault-health` | 신뢰도 감쇠 + 전체 감사 + 헬스 리포트 노드 |

### 빠른 참조

- 기본 namespace: `<namespace>`
- 기본 visibility: `<visibility>` (모델: `public` | `namespace` | `private` | `system`)
- 문서 언어: `한국어 (Korean)` — 사람이 읽는 모든 노드 콘텐츠(title, summary, body, edge `note`, 쿼리 답변, 헬스 리포트)를 한국어로 작성한다. 구조 어휘는 정규 영어로 유지: frontmatter 키, 위 노드/엣지 타입 이름, visibility 값, `id` 슬러그, namespace 이름, tags, 폴더명, 스킬/명령 이름. `_system/AGENTS.md` → Document Language 참고.
- 노드 타입: `pillar decision concept question playbook task event pattern hypothesis fact source bookmark note contact reference custom log`
- 엣지 타입: `related_to depends_on derived_from contradicts supports part_of preceded_by followed_by authored_by tagged_with`
- 에이전트 진입점: `_system/INDEX.md` — 모든 새 노드가 갱신해야 함
- 확립된 노드에 `edges: []`를 빈 채로 두지 말 것
- `raw/`는 불변 원자료 — 편집 금지; `/convert-note`가 처리된 원본을 `raw/processed/`로 옮긴다
- 모든 스킬 실행은 `logs/`에 로그 노드를 쓴다(축소된 8필드 스키마; 인덱싱·편집 안 함)
