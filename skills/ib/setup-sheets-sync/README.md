# Google Sheets 미러 (sheets-sync)

Infinite Brain 볼트(마크다운 = 진실의 원천)를 Google 스프레드시트(읽기 뷰)로
**push 시 변경분만** 동기화하는 템플릿. `setup-sheets-sync` 스킬이 이 폴더의 파일을
볼트 레포로 복사하고 Actions 설정을 안내한다. GCP 자격증명(프로젝트·서비스계정·키)은
`setup-gcp` 스킬이 1회 프로비저닝해 `~/.config/ib/sheets-sync.env` 에 저장하고 재사용한다.

## 동기화 전략 (왜 캐시 파일이 없나)

- **기준 상태 = 시트의 숨김 `_hash` 열.** 별도 캐시 파일을 두지 않는다.
  - GitHub Actions 러너는 매 실행이 새 VM(ephemeral) → 로컬 캐시 파일은 다음 실행 때 사라진다.
    레포에 커밋백하면 잡음 커밋·레이스, `actions/cache`는 만료/축출로 보장 불가.
  - 시트는 **영속적 공유 상태**라 스테이트리스 CI에 자연스럽게 맞고, 시트가 손편집돼
    어긋나도 해시 비교로 **자가 교정**된다.
- **변경 감지**: 노드·엣지 행을 정규화 후 `sha256` → 시트의 직전 해시와 다르면만 기록.
- **추가/삭제**: 키 집합 비교 (노드 키=`id`, 엣지 키=`source|type|target`).
- **반영**: 탭별 `batch_update`(변경) + `append_rows`(추가) + `deleteDimension`(삭제).
- **두 탭 정규화**: 노드는 `_data`, 관계는 `_edges`로 분리해 그래프 탐색에 최적화 —
  나가는 엣지=`source` 필터, 들어오는 엣지(백링크)=`target` 필터. 탭은 이름
  (`NODE_TAB`/`EDGE_TAB`)으로 찾고 첫 탭 폴백 없음. `_edges`는 없으면 생성.
- **읽기는 `id`+`_hash` 열만**(`batch_get`, body 등 본문 열 제외) → 행이 많아도 읽기 페이로드가 거의 안 늘어남. 해시가 본문까지 담고 있어 변경 감지에 본문 불필요.
- 1회 실행 비용 = (로컬 md 해시: 싸다) + (시트 키/해시 열만 읽기) + (바뀐 행만 쓰기).
- 상한: Google Sheets는 셀 1,000만 개(≈노드 50만 행)가 물리적 한계 — 그 이상은 그래프 DB 영역.
  규모가 매우 커지면 워크플로의 `paths:` 필터로 후보를 줄이거나, git diff 보조 레이어를
  얹을 수 있으나 **시트가 source of truth로 유지**되어야 한다.

## 시트 구성 (3 탭)

- **`_data`** (노드, 스캔용) — 프론트매터 15필드 + `body` + 숨김 `_hash`:
  `id, title, type, namespace, visibility, summary, auto_inject, applicable_when,
  confidence, verified_at, verified_by, staleness_signal, tags, related, source_url, body, _hash`
  `tags`·`related` 는 **쉼표 구분 텍스트**(JSON 아님). 관계는 여기 없고 `_edges`에 있다.
- **`_edges`** (관계, 평면) — `source | type | target | weight | note | _hash`.
  노드 frontmatter의 `edges` 를 sync가 펼쳐 자동 생성. 양방향 필터로 탐색.
- **`_meta`** (스키마 문서) — `sheet/_meta.csv`(레포에 보관하는 고정 문서)로 통째 갱신.

### git에 보관하는 CSV 스냅샷 (3개)

매 실행 시 볼트에서 **`sheet/_data.csv` · `sheet/_edges.csv`** 를 빌드한다(`_hash` 제외, 순수 텍스트).
git에 커밋해 두면 시트 상태가 버전관리·diff·머지 가능. `sheet/_meta.csv` 는 손으로 관리하는
스키마 문서(시드 제공). CI 워크플로는 변경된 CSV를 자동으로 커밋백한다.

### 동기화 방식 (`--method`)

- `api`(기본): 탭별 해시 비교로 **바뀐 행만** 기록(읽기는 `id`+`_hash` 열만).
- `overwrite`: 탭을 `clear` 후 **전체 일괄 쓰기**(단순·확실). 쓴 행에 `_hash`가 포함돼 이후 `api` 실행도 일관.

## 1회 설정 (자격증명은 setup-gcp가 1회·재사용, 연동은 setup-sheets-sync가 볼트별, ★ 2개만 사람이 클릭)

**A. `/setup-gcp` — 계정당 1회, 멱등(있으면 재사용):**
1. **GCP 프로젝트(기본 `infinite-brain`) + Google Sheets/Drive API** — gcloud 우선, 없으면 브라우저.
   이미 있으면 새로 만들지 않고 재사용(중복 프로젝트 생성 방지).
2. **서비스 계정 생성** → **JSON 키** … gcloud면 자동 생성, 브라우저면 ★ **다운로드는 사람이 클릭**(자격증명).
   `~/.config/ib/sheets-sync-sa.json` 에 저장하고 이후 재사용. 결과를 `~/.config/ib/sheets-sync.env` 에 영속화.

**B. `/setup-sheets-sync` — 볼트마다:**
3. **대상 스프레드시트** — 기본은 새 `지식` 시트 생성(Google Drive MCP), 기존 시트 재사용/다른 이름도 가능.
4. **대상 스프레드시트를 서비스 계정 이메일과 공유(편집자)** … ★ **사람이 권한 부여**.
5. 레포 설정 (`gh` 로 진행):
   - Secret `GOOGLE_SA_KEY` = JSON 키 내용
   - Variable `SPREADSHEET_ID` = 대상 시트 ID  (탭 이름은 `NODE_TAB`/`EDGE_TAB`로 변경 가능)
6. 볼트 레포로 `sync.py`·`requirements.txt`·`.github/workflows/sheets-sync.yml` 복사 후
   초기 동기화 → push.

## 로컬 실행

```bash
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
export SPREADSHEET_ID=...        # 대상 시트 ID
python sync.py --vault . --dry-run            # 계획만(쓰기 없음)
python sync.py --vault .                       # api 증분(기본) + CSV 빌드
python sync.py --vault . --method overwrite    # 탭 clear 후 전체 쓰기
python sync.py --vault . --rebuild             # api 방식에서 두 탭 비우고 재생성
# CSV 출력 폴더 변경: --csv-dir <경로>  (기본 <vault>/sheet)
```

## 테스트

네트워크/Google API 없이 전부 검증된다(38 케이스):

- `test_sync.py` — 순수 로직: 파싱·`content_hash`·`node_row`/`edge_rows`·`scan_vault`·CSV 라운드트립·`plan_changes`.
- `test_sync_io.py` — I/O 경로: gspread 워크시트/스프레드시트를 충실히 흉내내는 페이크(`fakes.py`)로
  `read_sheet`·`reconcile_api`·`reconcile_overwrite`·`push_meta`·`get_or_create_ws`·삭제 순서·숨김 열·
  그리고 `open_spreadsheet`를 모킹한 **`sync()` 엔드투엔드 라운드트립**(2차 실행 no-op)까지.

```bash
pip install pytest pyyaml
pytest skills/ib/setup-sheets-sync/tests/ -q
```

> 키 JSON(`*.json`)은 절대 커밋하지 말 것 — `.gitignore` 에 추가.
