"""Infinite Brain 볼트(진실의 원천) → Google Sheet(뷰) 해시 기반 증분 동기화.

마크다운 노드가 진실의 원천이고, 시트는 거기서 생성되는 읽기 뷰다.
볼트를 스캔해 각 노드의 콘텐츠 해시를 계산하고, 시트에 저장된 직전 해시와
비교하여 **실제로 바뀐 노드만** 최소 API 호출로 반영한다.

  · 변경 감지 : 콘텐츠 해시(정규화 후 sha256) → 같으면 skip
  · 추가/삭제 : id 집합 비교
  · 반영      : batch update / append / deleteDimension 각 1회
  · 기준 상태 : 시트의 숨김 `_hash` 열 (별도 캐시 파일 없음 → CI 스테이트리스에 안전,
                시트가 손편집돼 어긋나도 자동 교정)

노드 인식: 프론트매터에 `id` 와 `type` 이 둘 다 있는 .md 파일.
(`_system`, `_templates`, `_prompts`, `.git`, `.obsidian`, `.claude`, `raw` 제외)

환경변수:
  SPREADSHEET_ID (필수)      대상 스프레드시트 ID
  WORKSHEET_GID  (선택)      대상 탭 gid. 없으면 WORKSHEET_TITLE(기본 '_data') 탭
  WORKSHEET_TITLE(선택)      대상 탭 이름 (기본 '_data') — gid 미지정 시 사용
  인증: GOOGLE_SA_KEY(JSON 내용) 또는 GOOGLE_APPLICATION_CREDENTIALS(파일 경로)

사용:
  python sync.py --vault .            # 동기화
  python sync.py --vault . --dry-run  # 계획만 출력
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

FIELDS = [
    "id", "title", "type", "namespace", "visibility", "summary",
    "auto_inject", "applicable_when", "confidence", "verified_at",
    "verified_by", "staleness_signal", "tags", "edges", "related", "source_url",
]
COLUMNS = FIELDS + ["body", "_hash"]
ID_IDX = 0
HASH_IDX = len(COLUMNS) - 1

SKIP_DIRS = {"_system", "_templates", "_prompts", ".git", ".obsidian",
             ".claude", "raw", "node_modules"}
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ── 마크다운 파싱 ──────────────────────────────────────────────────────────
def parse_node(path: Path) -> dict | None:
    import yaml

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        return None
    if not isinstance(fm, dict) or not fm.get("id") or not fm.get("type"):
        return None
    fm["__body__"] = parts[2].strip()
    return fm


def _cell(field: str, fm: dict) -> str:
    if field == "body":
        return fm.get("__body__", "")
    val = fm.get(field, "")
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False, sort_keys=False)
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if val is None:
        return ""
    return str(val)


def node_to_row(fm: dict) -> list[str]:
    return [_cell(f, fm) for f in COLUMNS[:-1]]


def content_hash(row: list[str]) -> str:
    norm = [c.replace("\r\n", "\n").strip() for c in row]
    return hashlib.sha256(json.dumps(norm, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def scan_vault(vault: Path) -> dict[str, list[str]]:
    nodes: dict[str, list[str]] = {}
    for path in sorted(vault.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(vault).parts):
            continue
        fm = parse_node(path)
        if not fm:
            continue
        nid = str(fm["id"]).strip()
        if nid in nodes:
            sys.exit(f"중복 id '{nid}' (파일: {path})")
        row = node_to_row(fm)
        row.append(content_hash(row))
        nodes[nid] = row
    return nodes


# ── 시트 ──────────────────────────────────────────────────────────────────
def get_worksheet():
    import gspread
    from google.oauth2.service_account import Credentials

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    if not spreadsheet_id:
        sys.exit("SPREADSHEET_ID 환경변수가 필요합니다.")

    if os.environ.get("GOOGLE_SA_KEY"):
        creds = Credentials.from_service_account_info(
            json.loads(os.environ["GOOGLE_SA_KEY"]), scopes=SCOPES)
    elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        creds = Credentials.from_service_account_file(
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=SCOPES)
    else:
        sys.exit("인증 정보 없음: GOOGLE_SA_KEY 또는 "
                 "GOOGLE_APPLICATION_CREDENTIALS 환경변수를 설정하세요.")
    sh = gspread.authorize(creds).open_by_key(spreadsheet_id)
    gid = os.environ.get("WORKSHEET_GID")
    if gid:
        return sh.get_worksheet_by_id(int(gid))
    # gid 미지정 시 데이터 탭 이름으로(기본 '_data'). 첫 탭으로 폴백하지 않는다
    # — 첫 탭이 _meta 같은 스키마 문서면 덮어쓰는 사고가 나기 때문.
    title = os.environ.get("WORKSHEET_TITLE", "_data")
    try:
        return sh.worksheet(title)
    except gspread.WorksheetNotFound:
        sys.exit(f"대상 탭을 못 찾음. WORKSHEET_GID를 지정하거나 '{title}' 탭을 만드세요.")


def read_sheet(ws):
    values = ws.get_all_values()
    header = values[0] if values else []
    index: dict[str, tuple[int, str]] = {}
    for r, row in enumerate(values[1:], start=2):
        if not row or not row[ID_IDX].strip():
            continue
        nid = row[ID_IDX].strip()
        h = row[HASH_IDX] if len(row) > HASH_IDX else ""
        index[nid] = (r, h)
    return header, index


# ── 동기화 ────────────────────────────────────────────────────────────────
def sync(vault: Path, dry_run: bool, rebuild: bool = False) -> None:
    import gspread

    ws = get_worksheet()
    if rebuild and not dry_run:
        print("rebuild: 대상 탭을 싹 비우고 마크다운 기준으로 전체 재생성합니다.")
        ws.clear()
    elif rebuild:
        print("rebuild(dry-run): 실제로는 대상 탭을 비우고 전체 재생성합니다.")
    desired = scan_vault(vault)
    header, sheet_idx = read_sheet(ws)

    header_ok = header == COLUMNS
    to_add, to_update, unchanged = [], [], 0
    for nid, row in desired.items():
        if nid not in sheet_idx:
            to_add.append((nid, row))
        elif sheet_idx[nid][1] != row[HASH_IDX] or not header_ok:
            to_update.append((nid, sheet_idx[nid][0], row))
        else:
            unchanged += 1
    to_delete = [(nid, sheet_idx[nid][0]) for nid in sheet_idx if nid not in desired]

    print(f"볼트 노드 {len(desired)} | 시트 노드 {len(sheet_idx)}")
    print(f"  + 추가 {len(to_add)} | ~ 변경 {len(to_update)} | "
          f"- 삭제 {len(to_delete)} | = 유지 {unchanged}"
          + ("  (헤더 갱신 필요)" if not header_ok else ""))
    if dry_run:
        for nid, _ in to_add:        print(f"  [+] {nid}")
        for nid, _, _ in to_update:  print(f"  [~] {nid}")
        for nid, _ in to_delete:     print(f"  [-] {nid}")
        print("dry-run: 시트에 쓰지 않음.")
        return
    if header_ok and not (to_add or to_update or to_delete):
        print("변경 없음 — 동기화 생략.")
        return

    last = gspread.utils.rowcol_to_a1(1, len(COLUMNS)).rstrip("1")

    if not header_ok:
        ws.update(range_name=f"A1:{last}1", values=[COLUMNS], value_input_option="RAW")
        ws.spreadsheet.batch_update({"requests": [{"updateDimensionProperties": {
            "range": {"sheetId": ws.id, "dimension": "COLUMNS",
                      "startIndex": HASH_IDX, "endIndex": HASH_IDX + 1},
            "properties": {"hiddenByUser": True}, "fields": "hiddenByUser"}}]})
    if to_update:
        ws.batch_update(
            [{"range": f"A{r}:{last}{r}", "values": [row]} for _, r, row in to_update],
            value_input_option="RAW")
    if to_delete:
        reqs = [{"deleteDimension": {"range": {
            "sheetId": ws.id, "dimension": "ROWS", "startIndex": r - 1, "endIndex": r}}}
            for _, r in sorted(to_delete, key=lambda x: x[1], reverse=True)]
        ws.spreadsheet.batch_update({"requests": reqs})
    if to_add:
        ws.append_rows([row for _, row in to_add], value_input_option="RAW")

    print(f"동기화 완료: +{len(to_add)} ~{len(to_update)} -{len(to_delete)}")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="ib 볼트 → Google Sheet 해시 동기화")
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "."),
                    help="마크다운 볼트 루트 (기본: VAULT_DIR 또는 현재 폴더)")
    ap.add_argument("--dry-run", action="store_true", help="계획만 출력")
    ap.add_argument("--rebuild", action="store_true",
                    help="대상 탭을 싹 비우고 마크다운 기준으로 전체 재생성")
    args = ap.parse_args()
    vault = Path(args.vault)
    if not vault.is_dir():
        sys.exit(f"볼트 폴더를 찾을 수 없음: {vault}")
    sync(vault, args.dry_run, args.rebuild)


if __name__ == "__main__":
    main()
