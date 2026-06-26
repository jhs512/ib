# Google Sheets 미러 (sheets-sync)

Infinite Brain 볼트(마크다운 = 진실의 원천)를 Google 스프레드시트(읽기 뷰)로
**push 시 변경분만** 동기화하는 템플릿. `setup-ib` 스킬이 이 폴더의 파일을
볼트 레포로 복사하고 GCP/Actions 설정을 안내한다.

## 동기화 전략 (왜 캐시 파일이 없나)

- **기준 상태 = 시트의 숨김 `_hash` 열.** 별도 캐시 파일을 두지 않는다.
  - GitHub Actions 러너는 매 실행이 새 VM(ephemeral) → 로컬 캐시 파일은 다음 실행 때 사라진다.
    레포에 커밋백하면 잡음 커밋·레이스, `actions/cache`는 만료/축출로 보장 불가.
  - 시트는 **영속적 공유 상태**라 스테이트리스 CI에 자연스럽게 맞고, 시트가 손편집돼
    어긋나도 해시 비교로 **자가 교정**된다.
- **변경 감지**: 노드를 정규화 후 `sha256` → 시트의 직전 해시와 다르면만 기록.
- **추가/삭제**: 볼트와 시트의 `id` 집합 비교.
- **반영**: `batch_update`(변경) + `append_rows`(추가) + `deleteDimension`(삭제) 각 1회.
- **대상 탭**: `WORKSHEET_GID`로 gid를 주거나, 없으면 `WORKSHEET_TITLE`(기본 `_data`) 탭을 쓴다.
  첫 탭으로 폴백하지 않는다 — 첫 탭이 `_meta` 같은 스키마 문서면 덮어쓰는 사고를 막기 위함.
- 1회 실행 비용 = (로컬 md 해시: 싸다) + (시트 1회 읽기) + (바뀐 행만 쓰기).
  규모가 매우 커지면 워크플로의 `paths:` 필터로 후보를 줄이거나, git diff 보조 레이어를
  얹을 수 있으나 **시트가 source of truth로 유지**되어야 한다.

## 시트 열 구성

프론트매터 16필드 + `body`(원자적 본문) + `_hash`(숨김):

```
id, title, type, namespace, visibility, summary, auto_inject, applicable_when,
confidence, verified_at, verified_by, staleness_signal, tags, edges, related,
source_url, body, _hash
```

`tags`/`edges`/`related` 는 JSON 문자열로 셀에 저장된다.

## 1회 설정 (대부분 setup-ib가 자동, ★ 2개만 사람이 클릭)

1. **GCP 프로젝트 + Google Sheets API 사용 설정** (setup-ib가 브라우저로 진행)
2. **서비스 계정 생성** → **JSON 키 생성** … ★ **다운로드 버튼은 사람이 클릭**(자격증명)
3. **대상 스프레드시트를 서비스 계정 이메일과 공유(편집자)** … ★ **사람이 권한 부여**
4. 레포 설정 (setup-ib가 `gh` 로 진행):
   - Secret `GOOGLE_SA_KEY` = JSON 키 내용
   - Variable `SPREADSHEET_ID` = 대상 시트 ID  (필요시 `WORKSHEET_GID`)
5. 볼트 레포로 `sync.py`·`requirements.txt`·`.github/workflows/sheets-sync.yml` 복사 후
   초기 동기화 → push.

## 로컬 실행

```bash
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
export SPREADSHEET_ID=...        # 대상 시트 ID
python sync.py --vault . --dry-run   # 계획 확인
python sync.py --vault .             # 동기화
```

> 키 JSON(`*.json`)은 절대 커밋하지 말 것 — `.gitignore` 에 추가.
