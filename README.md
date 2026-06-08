# jhs512/skills

Claude Code · OpenCode · Codex · Cursor 등에서 쓰는 에이전트 스킬 저장소입니다.
[open agent skills 생태계](https://github.com/vercel-labs/skills)의 `skills` CLI로 설치합니다.

## 설치

```bash
# 저장소의 모든 스킬 설치
npx skills@latest add jhs512/skills --all

# 그룹(카테고리) 단위로 보기
npx skills@latest add jhs512/skills --list

# 특정 스킬만 설치
npx skills@latest add jhs512/skills --skill init-vault --skill query-vault

# 특정 에이전트에만 설치 (예: Claude Code)
npx skills@latest add jhs512/skills -a claude-code
```

## 그룹

스킬은 `skills/<group>/<name>/SKILL.md` 카탈로그 레이아웃으로 그룹화되어 있습니다.

### `ib` — Infinite Brain

AI-first Obsidian 지식그래프 볼트 운영 스킬. 자세한 내용은 [`skills/ib/README.md`](./skills/ib/README.md).

| 스킬 | 용도 |
|---|---|
| `init-vault` | 새 볼트 스캐폴딩 |
| `convert-note` | raw 자료 → 타입이 있는 원자 노드 |
| `query-vault` | 그래프 탐색 기반 질의응답 |
| `organize-vault` | 대화형 볼트 감사 |
| `vault-health` | 신뢰도 감쇠 + 감사 + 헬스 리포트 |

## 새 스킬 추가

1. `skills/<group>/<name>/SKILL.md` 경로로 폴더를 만듭니다.
2. `SKILL.md` 상단에 `name`, `description` frontmatter를 넣습니다 (필수).
3. 새 그룹을 만들면 `.claude-plugin/plugin.json`의 `skills` 배열과 이 README에 등록합니다.

```md
---
name: my-skill
description: 이 스킬이 하는 일 한 줄 설명.
---

# 본문 ...
```

---

원본 볼트 스킬 출처: [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain)
