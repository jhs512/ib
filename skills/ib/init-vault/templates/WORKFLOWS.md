# 볼트 워크플로우

Infinite Brain 자동화를 위한 에이전트 비종속적 워크플로우 정의. 각 워크플로우는 예약 작업이나 cron 실행을 지원하는 모든 에이전트가 트리거할 수 있다.

---

## vault-health

**트리거:** 매주(권장: 월요일 오전)
**스킬:** `/vault-health`
**출력:** `notes/note-vault-health-YYYYMMDD.md` + 갱신된 `_system/INDEX.md`

**하는 일:**
1. 90일 이상 검증되지 않은 노드에 신뢰도 감쇠를 적용한다
2. 고아 노드, 모순, 오래된 신호, 상호 링크 누락, 분류체계, 가시성, 요약 품질을 점검한다
3. 구조화된 상태 보고서를 `note` 노드로 작성한다
4. 어떤 수정이든 실행하기 전에 사람의 승인을 받기 위해 우선순위 조치를 제시한다

**두 가지 모드:**
- `/vault-health` — 대화형: 감쇠 + 점검 + 각 수정 전에 확인
- `/vault-health auto` — 자동: 감쇠 + 점검 + 보고서 노드만, 수정 없음, 확인 없음

**에이전트별 설정:**

### Claude Code
```bash
# 매주 일정을 등록하려면 한 번 실행한다(auto 모드, 확인 없음):
/schedule weekly /vault-health auto
```

### GitHub Actions
`.github/workflows/vault-health.yml`을 생성한다 — Claude Code CLI를 통해 cron에 따라 예약된 에이전트를 원격으로 트리거한다. 아래 GITHUB-ACTIONS 섹션을 참고한다.

### Cursor / Gemini CLI / Copilot
스킬은 이 볼트가 아니라 ib Claude Code 플러그인에 있다. Claude가 아닌 에이전트의 경우 `_system/AGENTS.md`(운영 규칙)를 가리키고 vault-health 스킬에 설명된 감쇠 규칙을 적용한다(`/vault-health` 1단계: 미검증 91~180일에 신뢰도 −0.1, 181~365일에 −0.2, 하한 0.1).

---

## convert-note (요청 시 실행, 예약 아님)

**트리거:** 수동 — `raw/`에 파일을 넣은 후 실행
**스킬:** `/convert-note`
**출력:** 각 폴더에 생성된 새 타입 노드 + 갱신된 `_system/INDEX.md`

타입 분류에 사람의 검토가 필요하므로 자동화는 권장하지 않는다.

---

## GITHUB-ACTIONS

`vault-health`를 GitHub Action으로 실행하려면(러너에 Claude Code CLI 설치 필요):

```yaml
# .github/workflows/vault-health.yml
name: Vault Health

on:
  schedule:
    - cron: '0 8 * * 1'   # 매주 월요일 08:00 UTC
  workflow_dispatch:        # 수동 트리거

jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run vault-health skill
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          npm install -g @anthropic-ai/claude-code
          claude --print --skill vault-health auto
      - name: Commit health report
        run: |
          git config user.name "vault-health[bot]"
          git config user.email "vault-health@users.noreply.github.com"
          git add notes/ _system/INDEX.md
          git diff --cached --quiet || git commit -m "chore: vault health report $(date +%Y-%m-%d)"
          git push
```

> **참고:** `--skill vault-health`는 Claude Code CLI가 플래그를 통한 스킬 호출을 지원해야 한다. 현재 CLI 문서를 확인한다 — 대안은 스킬 내용을 `--system-prompt`로 전달하는 것이다.

---

## 워크플로우 원칙

1. **자동화 단계는 절대 삭제하지 않는다.** 감쇠는 `confidence`만 수정한다. 점검은 수집만 한다. 수정은 사람의 승인이 필요하다.
2. **모든 자동 실행은 노드를 작성한다.** `notes/`의 상태 보고서가 볼트 내부에 감사 추적을 만든다.
3. **워크플로우는 추가적이다.** 새 자동화는 노드를 덮어쓰지 않고 작성해야 한다. 이전 상태 보고서는 ID에 날짜를 포함하여 보존된다.
