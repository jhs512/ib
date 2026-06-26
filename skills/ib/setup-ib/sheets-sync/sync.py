"""Infinite Brain 볼트(진실의 원천) → Google Sheets(뷰) 해시 기반 증분 동기화.

마크다운 노드가 진실의 원천이고, 시트는 거기서 생성되는 읽기 뷰다.
그래프 탐색에 최적화하기 위해 **노드와 엣지를 별도 탭으로 정규화**한다.

  · `_data`  : 노드(스캔용). id 별 1행. tags/related 는 쉼표 구분(불필요한 JSON 없음).
  · `_edges` : 관계(평면). source|type|target|weight|note. 노드 frontmatter에서 자동 생성.
               → "X에서 나가는" `source=X`, "X로 들어오는" `target=X` 모두 단순 필터로 탐색.
  · `_meta`  : 스키마 문서(이 스크립트가 건드리지 않음).

동기화 전략:
  · 변경 감지 : 행을 정규화 후 sha256 → 시트 직전 해시와 다르면만 기록
  · 추가/삭제 : 키 집합 비교 (노드 키=id, 엣지 키=source|type|target)
  · 반영      : 탭별 batch update / append / deleteDimension
  · 기준 상태 : 각 탭의 숨김 `_hash` 열 (별도 캐시 파일 없음 → 스테이트리스 CI에 안전, 자가 교정)

노드 인식: 프론트매터에 `id` 와 `type` 이 둘 다 있는 .md 파일.
(`_system`, `_templates`, `_prompts`, `.git`, `.obsidian`, `.claude`, `raw` 제외)

환경변수:
  SPREADSHEET_ID  (필수)   대상 스프레드시트 ID
  NODE_TAB        (선택)   노드 탭 이름 (기본 '_data')
  EDGE_TAB        (선택)   엣지 탭 이름 (기본 '_edges', 없으면 생성)
  인증: GOOGLE_SA_KEY(JSON 내용) 또는 GOOGLE_APPLICATION_CREDENTIALS(파일 경로)

사용:
  python sync.py --vault .            # 증분 동기화
  python sync.py --vault . --dry-run  # 계획만 출력
  python sync.py --vault . --rebuild  # 두 탭 싹 비우고 md 기준 전체 재생성
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# ── 탭/스키마 ──────────────────────────────────────────────────────────────
# 노드 탭: 프론트매터 15필드(edges 제외) + body + 숨김 _hash
NODE_FIELDS = [
    "id", "title", "type", "namespace", "visibility", "summary",
    "auto_inject", "applicable_when", "confidence", "verified_at",
    "verified_by", "staleness_signal", "tags", "related", "source_url",
]
NODE_COLUMNS = NODE_FIELDS + ["body", "_hash"]
# 엣지 탭: 정규화된 평면 관계 + 숨김 _hash
EDGE_COLUMNS = ["source", "type", "target", "weight", "note", "_hash"]
LIST_FIELDS = {"tags", "related"}  # 쉼표 구분으로 직렬화(JSON 아님)

SKIP_DIRS = {"_system", "_templates", "_prompts", ".git", ".obsidian",
             ".claude", "raw", "node_modules"}
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SEP = "\x1f"  # 복합 키 구분자


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


def _node_cell(field: str, fm: dict) -> str:
    if field == "body":
        return fm.get("__body__", "")
    val = fm.get(field, "")
    if field in LIST_FIELDS:  # 리스트 → 쉼표 구분(JSON 아님)
        if isinstance(val, (list, tuple)):
            return ", ".join(str(v) for v in val)
        return str(val or "")
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if val is None:
        return ""
    return str(val)


def content_hash(row: list[str]) -> str:
    norm = [c.replace("\r\n", "\n").strip() for c in row]
    return hashlib.sha256(json.dumps(norm, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def scan_vault(vault: Path):
    """볼트 → ({node_id: 노드행+hash}, {edge_key: 엣지행+hash})."""
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
            sys.exit(f"중복 id '{nid}' (파일: {path})")
        row = [_node_cell(f, fm) for f in NODE_COLUMNS[:-1]]
        row.append(content_hash(row))
        nodes[nid] = row
        # 엣지 펼치기
        for e in (fm.get("edges") or []):
            if not isinstance(e, dict) or not e.get("target"):
                continue
            erow = [nid, str(e.get("type", "")), str(e["target"]),
                    str(e.get("weight", "")), str(e.get("note", ""))]
            erow.append(content_hash(erow))
            key = SEP.join(erow[:3])  # source|type|target
            edges[key] = erow  # 동일 (source,type,target) 중복이면 마지막 우선
    return nodes, edges


# ── 시트 ──────────────────────────────────────────────────────────────────
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


def read_sheet(ws, key_cols, hash_idx, n_cols):
    """변경 감지에 필요한 **키 열 + `_hash` 열만** 읽는다(body 등 본문 열은 안 읽음).

    `_hash`가 이미 행 전체(본문 포함) 내용을 담고 있으므로, 변경 여부는 해시 비교로 충분.
    덕분에 행이 많아도 읽기 페이로드가 작다(읽기는 탭당 batch_get 1회).
    반환: (헤더, {key: (행번호1based, 기존해시)})
    """
    import gspread
    col = lambda i: gspread.utils.rowcol_to_a1(1, i + 1).rstrip("1")
    res = ws.batch_get([
        f"{col(0)}1:{col(n_cols - 1)}1",          # 헤더 행
        f"{col(key_cols[0])}2:{col(key_cols[-1])}",  # 키 열(들)
        f"{col(hash_idx)}2:{col(hash_idx)}",       # 해시 열
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


# ── 한 탭 reconcile ────────────────────────────────────────────────────────
def reconcile(ws, columns, key_cols, desired, dry_run, rebuild, label):
    import gspread

    hash_idx = len(columns) - 1
    if rebuild and not dry_run:
        ws.clear()
    header, sheet_idx = read_sheet(ws, key_cols, hash_idx, len(columns))
    header_ok = header == columns

    to_add, to_update, unchanged = [], [], 0
    for key, row in desired.items():
        if key not in sheet_idx:
            to_add.append(row)
        elif sheet_idx[key][1] != row[hash_idx] or not header_ok:
            to_update.append((sheet_idx[key][0], row))
        else:
            unchanged += 1
    to_delete = [pos for key, (pos, _) in sheet_idx.items() if key not in desired]

    print(f"[{label}] 볼트 {len(desired)} | 시트 {len(sheet_idx)} → "
          f"+추가 {len(to_add)} ~변경 {len(to_update)} -삭제 {len(to_delete)} "
          f"=유지 {unchanged}" + ("  (헤더 갱신)" if not header_ok else ""))
    if dry_run or (header_ok and not (to_add or to_update or to_delete)):
        return

    last = gspread.utils.rowcol_to_a1(1, len(columns)).rstrip("1")
    if not header_ok:
        ws.update(range_name=f"A1:{last}1", values=[columns], value_input_option="RAW")
        ws.spreadsheet.batch_update({"requests": [{"updateDimensionProperties": {
            "range": {"sheetId": ws.id, "dimension": "COLUMNS",
                      "startIndex": hash_idx, "endIndex": hash_idx + 1},
            "properties": {"hiddenByUser": True}, "fields": "hiddenByUser"}}]})
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


# ── 동기화 ────────────────────────────────────────────────────────────────
def sync(vault: Path, dry_run: bool, rebuild: bool) -> None:
    sh = open_spreadsheet()
    node_tab = os.environ.get("NODE_TAB", "_data")
    edge_tab = os.environ.get("EDGE_TAB", "_edges")
    nodes_ws = get_or_create_ws(sh, node_tab, len(NODE_COLUMNS))
    edges_ws = get_or_create_ws(sh, edge_tab, len(EDGE_COLUMNS))

    nodes, edges = scan_vault(vault)
    if rebuild:
        print("rebuild: 두 탭을 싹 비우고 마크다운 기준으로 전체 재생성"
              + (" (dry-run)" if dry_run else ""))
    reconcile(nodes_ws, NODE_COLUMNS, [0], nodes, dry_run, rebuild, node_tab)
    reconcile(edges_ws, EDGE_COLUMNS, [0, 1, 2], edges, dry_run, rebuild, edge_tab)
    if dry_run:
        print("dry-run: 시트에 쓰지 않음.")
    else:
        print("동기화 완료.")


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="ib 볼트 → Google Sheets 해시 동기화")
    ap.add_argument("--vault", default=os.environ.get("VAULT_DIR", "."),
                    help="마크다운 볼트 루트 (기본: VAULT_DIR 또는 현재 폴더)")
    ap.add_argument("--dry-run", action="store_true", help="계획만 출력")
    ap.add_argument("--rebuild", action="store_true",
                    help="두 탭을 싹 비우고 마크다운 기준으로 전체 재생성")
    args = ap.parse_args()
    vault = Path(args.vault)
    if not vault.is_dir():
        sys.exit(f"볼트 폴더를 찾을 수 없음: {vault}")
    sync(vault, args.dry_run, args.rebuild)


if __name__ == "__main__":
    main()
