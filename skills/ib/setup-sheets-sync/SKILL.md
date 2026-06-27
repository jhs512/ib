---
name: setup-sheets-sync
description: "현재 Infinite Brain 볼트의 Google Sheets 미러를 연결한다 — (기본으로) `지식` 이름의 Google Sheet 생성, 서비스 계정과 공유, 동기화 템플릿(sync.py, workflow, requirements, _meta)을 볼트 레포로 복사, `gh` secret/variable 설정, 초기 일방향 동기화 실행. 마크다운 볼트가 진실의 원천으로 유지되고, GitHub Action이 push마다 변경된 노드/엣지만 다시 동기화한다. 브라우저 자동화(예: Claude in Chrome)는 하드 전제다 — 스킬은 맨 처음 활성화 여부를 확인하고 꺼져 있으면 즉시 중단한다. `setup-gcp` 의 재사용 가능한 Google Cloud 자격증명(먼저 1회 실행)과, 볼트가 `gh` 인증된 GitHub 레포일 것을 요구한다. 스프레드시트는 기본으로 `지식` 제목의 새 시트를 만들며, 사용자는 기존 시트를 재사용하거나 다른 이름을 고를 수 있다."
disable-model-invocation: true
---

# 이 볼트의 Google Sheets 미러 설정

이것은 Sheets 미러의 **볼트별** 절반이다. 재사용 가능한 계정 수준 자격증명(GCP 프로젝트, 서비스 계정, JSON 키)은 **`/setup-gcp`** 에서 온다 — 먼저 1회 실행할 것. 이 스킬은 그다음 *이* 볼트를 스프레드시트에 연결한다.

마크다운 볼트가 진실의 원천이고, 시트는 생성된 **읽기 뷰**다. GitHub Action이 push마다 변경된 노드/엣지만 다시 동기화한다(콘텐츠 해시 기반, 캐시 파일 없음 — 기준 해시는 각 탭의 숨김 `_hash` 열에 산다). 근거와 무캐시 설계: [README.md](./README.md).

## 0. 브라우저 자동화는 켜져 있어야 한다 — 가장 먼저 확인 (하드 게이트)

이 스킬은 브라우저 사용을 전제한다. **다른 무엇이든 하기 전에**, 브라우저 구동 도구가 사용 가능하고 활성화돼 있는지 확인한다 — `claude-in-chrome` 스킬 또는 Chrome/DevTools MCP.

- **활성화됨** → 전제 조건으로 진행.
- **활성화 안 됨** → **즉시 중단.** 사용자에게 브라우저 자동화를 켜라고 알린다(**Claude in Chrome** 확장 / Chrome MCP 권장) 그리고 다시 실행하게 한다. 미러를 절반만 연결하고 공유/콘솔 단계에서 실패하지 말 것.

(시트 생성은 브라우저 없이 Google Drive 도구로 진행될 수 있으나, 공유 단계와 콘솔/시트 상호작용에는 브라우저 사용이 필요하므로, 실행 중간에 발견하는 대신 맨 앞에서 요구한다.)

## 1. 전제 조건

- **ib 컨텍스트 존재** — 이 디렉터리에 있어야 한다(없으면 먼저 `/setup-ib` 실행).
- **GCP 자격증명 존재.** `~/.config/ib/sheets-sync.env` 를 읽는다. 없거나 불완전하면(`GCP_PROJECT_ID`, `SA_EMAIL`, `SA_KEY_PATH`), 중단하고 사용자에게 먼저 **`/setup-gcp`** 를 실행하라고 알린다(호출 제안 가능). 거기서 `SA_EMAIL` 과 `SA_KEY_PATH` 를 로드한다.
- **GitHub 레포 + `gh`.** 볼트가 GitHub 레포이고 `gh` 가 `repo` + `workflow` 스코프로 인증돼 있어야 한다(`gh auth status`). `/setup-ib` 가 기본으로 이를 설정한다. **`gh` 가 설치돼 있지 않으면 먼저 설치를 안내한다** — <https://cli.github.com/>(Windows: `winget install GitHub.cli`, macOS: `brew install gh`), 그다음 `gh auth login`(세션에서 바로 보려면 `! gh auth login`). 볼트가 어쩌다 git 레포가 아니거나 아직 GitHub 리모트가 없으면, 중단하지 말고 지금 생성을 제안한다(`git init` / `gh repo create <name> --private --source=. --remote=origin`) — 미러의 GitHub Action에 필요하다.

볼트가 더 큰 레포의 하위 폴더에 있으면 볼트 폴더를 기록한다 — 워크플로와 로컬 실행에서 `--vault <folder>` 가 된다.

## 2. 대상 스프레드시트 선택 (기본: 새 `지식` 시트)

두 탭은 **이름으로** 관리된다: `_data`(노드: frontmatter 15필드 + `body` + 숨김 `_hash`; `tags`/`related` 는 JSON이 아니라 쉼표 구분) 과 `_edges`(정규화된 관계 `source | type | target | weight | note`, 각 노드의 `edges` 에서 자동 생성). `_meta` 스키마 탭이 있으면 그대로 둔다. 탭 이름은 나중에 `NODE_TAB`/`EDGE_TAB` 로 변경할 수 있다.

생성/조회에는 **Google Drive MCP 도구** 를 우선 사용한다. 없으면 브라우저로 `sheets.new` 를 구동한다(§0에서 브라우저 사용이 이미 확인됨).

1. **먼저 기존 시트를 찾는다**(멱등 유지). Drive에서 `지식` 이름의 스프레드시트를 검색한다:
   - `mcp__claude_ai_Google_Drive__search_files` 로 이름 `지식`(mimeType `application/vnd.google-apps.spreadsheet`) 검색.
   - 하나 이상 발견되면 사용자에게 묻는다: **재사용**(그 id 사용) 또는 **그래도 새로 생성**.
2. **기본 — `지식` 제목의 새 시트 생성**("Knowledge") — 없거나 사용자가 새 시트를 원할 때:
   - `mcp__claude_ai_Google_Drive__create_file` 에 mimeType `application/vnd.google-apps.spreadsheet`, 이름 `지식`.
   - 사용자는 **다른 이름**을 고르거나, 대신 사용할 **기존 시트의 URL/ID** 를 제공할 수 있다.
3. **`SPREADSHEET_ID` 확보** — 파일 id / URL(`https://docs.google.com/spreadsheets/d/<ID>/edit`)에서.

## 3. 스프레드시트를 서비스 계정과 공유 — ★ 사람만

동기화는 서비스 계정으로 인증하므로, 시트가 그 계정에 접근 권한을 부여해야 한다. 권한을 추가하는 Drive MCP 도구는 없고, 어느 쪽이든 권한 변경이므로 **사용자가 직접** 한다:

1. 대상 스프레드시트를 연다.
2. **공유**(우상단)를 클릭한다.
3. `~/.config/ib/sheets-sync.env` 의 `SA_EMAIL` 을 붙여넣는다.
4. 역할을 **편집자**로 설정하고, "사용자에게 알림" 이 보이면 해제한 뒤 **보내기 / 공유**.

이것 없이는 동기화가 `403 PERMISSION_DENIED` 로 실패한다. 계속하기 전에 사용자가 완료했는지 확인한다.

## 4. 동기화 템플릿을 볼트 레포로 복사

이 스킬 폴더에서 볼트로:

- [`sync.py`](./sync.py) → 볼트 루트 `sync.py`
- [`requirements.txt`](./requirements.txt) → 볼트 루트 `requirements.txt`(이미 있으면 병합)
- [`sheets-sync.yml`](./sheets-sync.yml) → `.github/workflows/sheets-sync.yml`
- [`_meta.csv`](./_meta.csv) → `sheet/_meta.csv`(`_meta` 탭을 채우는 스키마 문서; 원하면 나중에 편집)
- [`tests/`](./tests/) → `tests/`(선택 — 네트워크 없는 단위 테스트)

그런 다음:
- `.gitignore` 에 `*.json` 이 포함되도록 재확인한다(`/setup-ib`가 기준선으로 이미 넣지만, 없으면 추가 — 서비스 계정 키는 절대 커밋 금지).
- 볼트가 하위 폴더에 있으면 워크플로의 실행 스텝에 `--vault <folder>` 를 설정한다.

각 동기화는 `sheet/_data.csv` + `sheet/_edges.csv`(시트의 git 추적 스냅샷)를 빌드한다. 이들은 커밋된다.

## 5. `gh` 로 레포 연동

- `gh secret set GOOGLE_SA_KEY < "$SA_KEY_PATH"`(암호화 업로드; 출력되거나 커밋되지 않음).
- `gh variable set SPREADSHEET_ID --body <spreadsheet-id>`(탭 이름은 기본 `_data`/`_edges`; 변경 시에만 `NODE_TAB`/`EDGE_TAB` variable 설정).

## 6. 초기 동기화 + push

- 먼저 로컬에서 검증한다:
  ```bash
  SPREADSHEET_ID=… GOOGLE_APPLICATION_CREDENTIALS="$SA_KEY_PATH" python sync.py --vault <vault> --dry-run
  ```
  그다음 `--dry-run` 없이 실행한다(기본 `--method api`; `--method overwrite` 는 각 탭을 비우고 다시 쓴다).
- 템플릿 **과 생성된 `sheet/*.csv` 스냅샷**을 커밋한 뒤 push → **Sheets Sync** Action이 이후 모든 push에서 변경된 노드/엣지만 반영한다(그리고 갱신된 CSV 스냅샷을 다시 커밋백한다).

## 7. 완료

무엇이 연결됐는지 보고한다: 스프레드시트 URL/id, 공유된 서비스 계정 이메일, `gh` secret/variable 이름. 이제 push가 변경된 노드를 시트에 자동 동기화함을 알린다. 키 파일(`SA_KEY_PATH`)은 안전하게 보관해야 할 라이브 자격증명임을 사용자에게 상기시킨다(또는 나중에 `/setup-gcp` 로 회전). GCP 자격증명은 재사용 가능하므로, *다른* 볼트의 미러 설정은 이 스킬을 다시 실행하기만 하면 된다 — `/setup-gcp` 는 불필요하다.
