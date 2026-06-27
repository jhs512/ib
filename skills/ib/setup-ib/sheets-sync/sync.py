"""Infinite Brain 볼트(진실의 원천) → Google Sheets(뷰) 동기화.

마크다운 노드가 진실의 원천이고, 시트는 거기서 생성되는 읽기 뷰다.
그래프 탐색에 최적화하기 위해 노드와 엣지를 별도 탭으로 정규화한다.

  · `_data`  : 노드(스캔용). id 별 1행. tags/related 는 쉼표 구분(불필요한 JSON 없음).
  · `_edges` : 관계(평면). source|type|target|weight|note. 노드 frontmatter에서 자동 생성.
  · `_meta`  : 스키마 문서. `sheet/_meta.csv`(있으면)로 덮어쓴다.

매 실행 시 볼트에서 **CSV 3개**(`sheet/_data.csv`, `sheet/_edges.csv`)를 빌드해 둔다 — git에
보관·diff 가능한 시트 스냅샷. (`_meta.csv`는 손으로 관리하는 고정 스키마 문서.)

동기화 방식(--method):
  · api(기본) : 탭별 해시 비교로 **바뀐 행만** 기록. 읽기는 id+_hash 열만(본문 안 읽음).
  · overwrite : 탭을 clear 후 **전체 일괄 쓰기**(단순·확실).

노드 인식: 프론트매터에 `id` 와 `type` 이 둘 다 있는 .md 파일.
(`_system`, `_templates`, `_prompts`, `.git`, `.obsidian`, `.claude`, `raw` 제외)

환경변수:
  SPREADSHEET_ID (필수)  대상 스프레드시트 ID
  NODE_TAB/EDGE_TAB/META_TAB (선택)  탭 이름(기본 _data/_edges/_meta)
  CSV_DIR (선택)  CSV 출력 폴더(기본 <vault>/sheet)
  인증: GOOGLE_SA_KEY(JSON 내용) 또는 GOOGLE_APPLICATION_CREDENTIALS(파일 경로)

사용:
  python sync.py --vault .                      # api 증분(기본) + CSV 빌드
  python sync.py --vault . --dry-run            # 계획만(쓰기 없음)
  python sync.py --vault . --method overwrite   # 탭 clear 후 전체 쓰기
  python sync.py --vault . --rebuild            # api 방식에서 두 탭 비우고 재생성
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

# ── 탭/스키마 ──────────────────────────────────────────────────────────────
NODE_FIELDS = [
    "id", "title", "type", "namespace", "visibility", "summary",
    "auto_inject", "applicable_when", "confidence", "verified_at",
    "verified_by", "staleness_signal", "tags", "related", "source_url",
]
NODE_COLUMNS = NODE_FIELDS + ["body", "_hash"]          # 시트/스캔용(해시 포함)
EDGE_COLUMNS = ["source", "type", "target", "weight", "note", "_hash"]
LIST_FIELDS = {"tags", "related"}                       # 쉼표 구분(JSON 아님)

SKIP_DIRS = {"_system", "_templates", "_prompts", ".git", ".obsidian",
             ".claude", "raw", "node_modules"}
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SEP = "\x1f"  # 복합 키 구분자


# ── 마크다운 파싱(순수) ────────────────────────────────────────────────────
def parse_node(path: Path) -> dict | None:
    import yaml

    text = Path(path).read_text(encoding="utf-8")
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


def _node_cell(field: str, fm: dict) -> str:
    if field == "body":
        return fm.get("__body__", "")
    val = fm.get(field, "")
    if field in LIST_FIELDS:
        if isinstance(val, (list, tuple)):
            return ", ".join(str(v) for v in val)
        return str(val or "")
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if val is None:
        return ""
    return str(val)


def content_hash(row) -> str:
    norm = [str(c).replace("\r\n", "\n").strip() for c in row]
    return hashlib.sha256(json.dumps(norm, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def node_row(fm: dict) -> list[str]:
    """노드 frontmatter → _data 행(해시 포함, 마지막 열)."""
    row = [_node_cell(f, fm) for f in NODE_COLUMNS[:-1]]
    row.append(content_hash(row))
    return row


def edge_rows(fm: dict):
    """노드 frontmatter → 엣지 행 리스트(각 해시 포함)."""
    src = str(fm["id"]).strip()
    out = []
    for e in (fm.get("edges") or []):
        if not isinstance(e, dict) or not e.get("target"):
            continue
        erow = [src, str(e.get("type", "")), str(e["target"]),
                str(e.get("weight", "")), str(e.get("note", ""))]
        erow.append(content_hash(erow))
        out.append(erow)
    return out


def scan_vault(vault: Path):
    """볼트 → ({node_id: 노드행+hash}, {edge_key: 엣지행+hash})."""
    vault = Path(vault)
    nodes: dict[str, list[str]] = {}
    edges: dict[str, list[str]] = {}
    for path in sorted(vault.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.relative_to(vault).parts):
            continue
        fm = parse_node(path)
        if not fm:
            continue
        nid = str(fm["id"]).strip()
        if nid in nodes:
            raise ValueError(f"중복 id '{nid}' (파일: {path})")
        nodes[nid] = node_row(fm)
        for erow in edge_rows(fm):
            edges[SEP.join(erow[:3])] = erow  # source|type|target, 중복이면 마지막
    return nodes, edges


# ── CSV 빌드(순수, git 산출물) ──────────────────────────────────────────────
def _write_csv(path: Path, header, rows) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def build_csvs(nodes, edges, csv_dir: Path) -> None:
    """git에 보관할 시트 스냅샷(_data.csv, _edges.csv) 생성. _hash 열은 제외."""
    csv_dir = Path(csv_dir)
    csv_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(csv_dir / "_data.csv", NODE_COLUMNS[:-1],
               [r[:-1] for r in nodes.values()])
    _write_csv(csv_dir / "_edges.csv", EDGE_COLUMNS[:-1],
               [r[:-1] for r in edges.values()])


def read_csv_rows(path: Path):
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        return [row for row in csv.reader(f)]


# ── diff 계획(순수) ────────────────────────────────────────────────────────
def plan_changes(desired, sheet_index, header_ok, hash_idx):
    """(to_add, to_update[(row,vals)], to_delete[row], unchanged) 계산. 순수 함수."""
    to_add, to_update, unchanged = [], [], 0
    for key, row in desired.items():
        if key not in sheet_index:
            to_add.append(row)
        elif sheet_index[key][1] != row[hash_idx] or not header_ok:
            to_update.append((sheet_index[key][0], row))
        else:
            unchanged += 1
    to_delete = [pos for key, (pos, _) in sheet_index.items() if key not in desired]
    return to_add, to_update, to_delete, unchanged


# ── 시트 I/O ───────────────────────────────────────────────────────────────
def open_spreadsheet():
    import gspread
    from google.oauth2.service_account import Credentials

    sid = os.environ.get("SPREADSHEET_ID")
    if not sid:
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
    return gspread.authorize(creds).open_by_key(sid)


def get_or_create_ws(sh, title: str, cols: int):
    import gspread
    try:
        return sh.worksheet(title)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=title, rows=100, cols=cols)


def _col(i: int) -> str:
    import gspread
    return gspread.utils.rowcol_to_a1(1, i + 1).rstrip("1")


def read_sheet(ws, key_cols, hash_idx, n_cols):
    """변경 감지용으로 **키 열 + `_hash` 열만** 읽는다(본문 열 제외)."""
    res = ws.batch_get([
        f"{_col(0)}1:{_col(n_cols - 1)}1",
        f"{_col(key_cols[0])}2:{_col(key_cols[-1])}",
        f"{_col(hash_idx)}2:{_col(hash_idx)}",
    ])
    header = list(res[0][0]) if len(res) > 0 and res[0] else []
    keyvals = res[1] if len(res) > 1 else []
    hashvals = res[2] if len(res) > 2 else []
    index: dict[str, tuple[int, str]] = {}
    nkeys = len(key_cols)
    for i, krow in enumerate(keyvals):
        if not krow or not krow[0].strip():
            continue
        key = SEP.join((krow[j] if j < len(krow) else "") for j in range(nkeys))
        h = hashvals[i][0] if i < len(hashvals) and hashvals[i] else ""
        index[key] = (i + 2, h)
    return header, index


def _hide_hash_col(ws, hash_idx):
    ws.spreadsheet.batch_update({"requests": [{"updateDimensionProperties": {
        "range": {"sheetId": ws.id, "dimension": "COLUMNS",
                  "startIndex": hash_idx, "endIndex": hash_idx + 1},
        "properties": {"hiddenByUser": True}, "fields": "hiddenByUser"}}]})


def reconcile_api(ws, columns, key_cols, desired, dry_run, rebuild, label):
    """해시 증분 동기화."""
    hash_idx = len(columns) - 1
    if rebuild and not dry_run:
        ws.clear()
    header, sheet_idx = read_sheet(ws, key_cols, hash_idx, len(columns))
    header_ok = header == columns
    to_add, to_update, to_delete, unchanged = plan_changes(
        desired, sheet_idx, header_ok, hash_idx)
    print(f"[{label}] 볼트 {len(desired)} | 시트 {len(sheet_idx)} → "
          f"+추가 {len(to_add)} ~변경 {len(to_update)} -삭제 {len(to_delete)} "
          f"=유지 {unchanged}" + ("  (헤더 갱신)" if not header_ok else ""))
    if dry_run or (header_ok and not (to_add or to_update or to_delete)):
        return
    last = _col(len(columns) - 1)
    if not header_ok:
        ws.update(range_name=f"A1:{last}1", values=[columns], value_input_option="RAW")
        _hide_hash_col(ws, hash_idx)
    if to_update:
        ws.batch_update([{"range": f"A{r}:{last}{r}", "values": [row]}
                         for r, row in to_update], value_input_option="RAW")
    if to_delete:
        reqs = [{"deleteDimension": {"range": {
            "sheetId": ws.id, "dimension": "ROWS", "startIndex": r - 1, "endIndex": r}}}
            for r in sorted(to_delete, reverse=True)]
        ws.spreadsheet.batch_update({"requests": reqs})
    if to_add:
        ws.append_rows(to_add, value_input_option="RAW")


def reconcile_overwrite(ws, columns, desired, dry_run, label):
    """탭 clear 후 전체 일괄 쓰기."""
    rows = list(desired.values())
    print(f"[{label}] overwrite → 헤더 + {len(rows)}행 전체 쓰기")
    if dry_run:
        return
    ws.clear()
    ws.update(range_name="A1", values=[columns] + rows, value_input_option="RAW")
    _hide_hash_col(ws, len(columns) - 1)


def push_meta(sh, csv_path: Path, dry_run, tab: str) -> None:
    """`_meta.csv`(있으면)로 _meta 탭을 통째 갱신."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return
    rows = read_csv_rows(csv_path)
    print(f"[{tab}] _meta.csv → {max(len(rows) - 1, 0)}행 overwrite")
    if dry_run or not rows:
        return
    ws = get_or_create_ws(sh, tab, max((len(r) for r in rows), default=4))
    ws.clear()
    ws.update(range_name="A1", values=rows, value_input_option="RAW")


# ── 동기화 ────────────────────────────────────────────────────────────────
def sync(vault: Path, dry_run: bool, rebuild: bool, method: str, csv_dir: Path) -> None:
    nodes, edges = scan_vault(vault)
    sh = open_spreadsheet()
    node_tab = os.environ.get("NODE_TAB", "_data")
    edge_tab = os.environ.get("EDGE_TAB", "_edges")
    meta_tab = os.environ.get("META_TAB", "_meta")

    if not dry_run:
        build_csvs(nodes, edges, csv_dir)
        print(f"CSV 빌드: {csv_dir}/_data.csv ({len(nodes)}), _edges.csv ({len(edges)})")

    nodes_ws = get_or_create_ws(sh, node_tab, len(NODE_COLUMNS))
    edges_ws = get_or_create_ws(sh, edge_tab, len(EDGE_COLUMNS))
    if method == "overwrite":
        reconcile_overwrite(nodes_ws, NODE_COLUMNS, nodes, dry_run, node_tab)
        reconcile_overwrite(edges_ws, EDGE_COLUMNS, edges, dry_run, edge_tab)
    else:
        reconcile_api(nodes_ws, NODE_COLUMNS, [0], nodes, dry_run, rebuild, node_tab)
        reconcile_api(edges_ws, EDGE_COLUMNS, [0, 1, 2], edges, dry_run, rebuild, edge_tab)
    push_meta(sh, Path(csv_dir) / "_meta.csv", dry_run, meta_tab)
    print("dry-run: 시트에 쓰지 않음." if dry_run else "동기화 완료.")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="ib 볼트 → Google Sheets 동기화")
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "."),
                    help="마크다운 볼트 루트 (기본: VAULT_DIR 또는 현재 폴더)")
    ap.add_argument("--csv-dir", default=os.environ.get("CSV_DIR"),
                    help="CSV 출력 폴더 (기본 <vault>/sheet)")
    ap.add_argument("--method", choices=["api", "overwrite"], default="api",
                    help="api=해시 증분(기본) / overwrite=탭 clear 후 전체 쓰기")
    ap.add_argument("--dry-run", action="store_true", help="계획만 출력")
    ap.add_argument("--rebuild", action="store_true",
                    help="api 방식에서 두 탭을 비우고 전체 재생성")
    args = ap.parse_args()
    vault = Path(args.vault)
    if not vault.is_dir():
        sys.exit(f"볼트 폴더를 찾을 수 없음: {vault}")
    csv_dir = Path(args.csv_dir) if args.csv_dir else vault / "sheet"
    sync(vault, args.dry_run, args.rebuild, args.method, csv_dir)


if __name__ == "__main__":
    main()
