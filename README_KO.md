<p align="center">
  <img src="https://img.shields.io/badge/Version-0.2.0-brightgreen.svg" alt="Version">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-purple.svg" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/Skills-6-orange.svg" alt="6 Skills">
  <img src="https://img.shields.io/badge/Vault-Obsidian_호환-7c3aed.svg" alt="Obsidian Compatible">
  <a href="https://github.com/jhs512/skills/stargazers"><img src="https://img.shields.io/github/stars/jhs512/skills?style=social" alt="GitHub Stars"></a>
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
| `/setup-ib` | 임의의 repo/폴더에 볼트 운영 컨텍스트 셋업 (최초 1회) |
| `/init-vault` | 완전한 볼트 스캐폴딩 — 폴더 17개, 시스템 스키마, 템플릿, 예시 노드 |
| `/convert-note` | `raw/`의 원자료를 원자적 타입 노드로 분해 |
| `/query-vault` | 그래프 탐색으로 질의응답 — 토큰 절약형 범위 검색 |
| `/organize-vault` | 대화형 감사: 고아 노드, 모순, 신뢰도 갭, 태그 난립 |
| `/vault-health` | 자동 유지보수: 신뢰도 감쇠 + 전체 감사 + 헬스 리포트 (`auto` 모드는 크론용) |

## 설치

### Claude Code 플러그인 (마켓플레이스)

```shell
/plugin marketplace add jhs512/skills
/plugin install infinite-brain@jhs512-skills
```

### skills CLI (Claude Code · Codex · Cursor · OpenCode)

```bash
# 전부 설치
npx skills@latest add jhs512/skills --all

# 골라서 설치
npx skills@latest add jhs512/skills --skill init-vault --skill query-vault

# 특정 에이전트에만
npx skills@latest add jhs512/skills -a claude-code
```

## 퀵스타트

```
1.  /setup-ib          # 1회 — 에이전트에게 "이 폴더는 볼트"라고 알림
2.  /init-vault        # 폴더·스키마·템플릿·예시 노드 2개 스캐폴딩
3.  raw/에 아무거나 투하   (아티클, 회의록, 녹취록 — 파일명만 잘 지으면 끝)
4.  /convert-note      # raw 파일 → 엣지로 연결된 원자적 타입 노드
5.  /query-vault       # 질문하면 에이전트가 그래프를 탐색
6.  /schedule weekly /vault-health auto    # 선택: 스스로 관리되는 기억
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
    ├── setup-ib/        #   온보딩 + 에이전트 규칙 시드
    ├── init-vault/      #   스캐폴더 + 동봉된 시스템 템플릿
    ├── convert-note/    #   raw → 원자 노드
    ├── query-vault/     #   범위 제한 그래프 검색
    ├── organize-vault/  #   대화형 감사
    └── vault-health/    #   감쇠 + 감사 + 리포트 (크론 지원)
.claude-plugin/
    ├── plugin.json      # Claude Code 플러그인 매니페스트
    └── marketplace.json # 마켓플레이스 등록 정보
```

새 스킬 추가: `skills/<group>/<name>/SKILL.md`를 만들고 frontmatter에 `name`·`description`을 넣은 뒤, 새 그룹이라면 `.claude-plugin/plugin.json`에 등록합니다.

## 크레딧 & 라이선스

[JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain)의 Infinite Brain 방법론 기반이며, [AI Impact — How to Build an Infinite Brain with AI](https://www.youtube.com/watch?v=z02Y-1OvWSM)에서 영감을 받았습니다.

[MIT](LICENSE)
