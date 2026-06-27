"""sync.py I/O 경로 테스트 — gspread를 FakeSpreadsheet/FakeWorksheet로 모킹(네트워크 없음).

read_sheet / reconcile_api / reconcile_overwrite / push_meta / get_or_create_ws /
_hide_hash_col / 삭제 순서 / sync() 엔드투엔드 라운드트립까지 검증.
"""
import pytest

import sync
from fakes import FakeSpreadsheet

NCOLS = len(sync.NODE_COLUMNS)
NHASH = NCOLS - 1
ECOLS = len(sync.EDGE_COLUMNS)
EHASH = ECOLS - 1


def node(id_, summary="s"):
    return sync.node_row({"id": id_, "type": "fact", "title": id_,
                          "summary": summary, "__body__": "b " + summary})


def edge(src, tgt, typ="supports", note="n"):
    fm = {"id": src, "type": "fact",
          "edges": [{"target": tgt, "type": typ, "weight": 0.5, "note": note}]}
    return sync.edge_rows(fm)[0]


def populate(ws, columns, rows):
    ws.grid = [list(columns)] + [list(r) for r in rows]


def ids_in(ws, key_cols, hash_idx, ncols):
    _, idx = sync.read_sheet(ws, key_cols, hash_idx, ncols)
    return idx


# ── read_sheet ──────────────────────────────────────────────────────────────
def test_read_sheet_parses_header_and_index():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    a, b = node("a"), node("b")
    populate(ws, sync.NODE_COLUMNS, [a, b])
    header, idx = sync.read_sheet(ws, [0], NHASH, NCOLS)
    assert header == sync.NODE_COLUMNS
    assert idx["a"] == (2, a[NHASH])
    assert idx["b"] == (3, b[NHASH])


def test_read_sheet_empty():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    header, idx = sync.read_sheet(ws, [0], NHASH, NCOLS)
    assert header == [] and idx == {}


def test_read_sheet_composite_edge_key():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_edges", 100, ECOLS)
    populate(ws, sync.EDGE_COLUMNS, [edge("a", "b")])
    _, idx = sync.read_sheet(ws, [0, 1, 2], EHASH, ECOLS)
    assert ("a" + sync.SEP + "supports" + sync.SEP + "b") in idx


def test_read_sheet_missing_hash_treated_empty():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    a = node("a")
    a_no_hash = a[:NHASH] + [""]            # 해시 칸 비어 있음
    populate(ws, sync.NODE_COLUMNS, [a_no_hash])
    _, idx = sync.read_sheet(ws, [0], NHASH, NCOLS)
    assert idx["a"] == (2, "")


# ── reconcile_api ───────────────────────────────────────────────────────────
def test_api_initial_populate():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    sync.reconcile_api(ws, sync.NODE_COLUMNS, [0], {"a": node("a"), "b": node("b")},
                       False, False, "_data")
    assert ws.n_clear == 0
    assert ws.grid[0] == sync.NODE_COLUMNS
    assert set(ids_in(ws, [0], NHASH, NCOLS)) == {"a", "b"}
    assert NHASH in ws.hidden_cols           # 해시 열 숨김 적용


def test_api_noop_when_unchanged():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    a = node("a"); populate(ws, sync.NODE_COLUMNS, [a])
    before = [r[:] for r in ws.grid]
    sync.reconcile_api(ws, sync.NODE_COLUMNS, [0], {"a": a}, False, False, "_data")
    assert ws.grid == before and ws.n_clear == 0 and ws.appended == []
    assert ss.requests == []                 # 쓰기 요청 전혀 없음


def test_api_update_add_delete():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    a, b, c = node("a", "v1"), node("b", "v1"), node("c", "v1")
    populate(ws, sync.NODE_COLUMNS, [a, b, c])
    desired = {"a": a, "b": node("b", "v2"), "d": node("d", "v1")}
    sync.reconcile_api(ws, sync.NODE_COLUMNS, [0], desired, False, False, "_data")
    _, idx = sync.read_sheet(ws, [0], NHASH, NCOLS)
    assert set(idx) == {"a", "b", "d"}        # c 삭제, d 추가
    assert idx["b"][1] == desired["b"][NHASH]  # b 해시 갱신됨
    assert idx["a"][1] == a[NHASH]            # a 그대로


def test_api_dry_run_writes_nothing():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    populate(ws, sync.NODE_COLUMNS, [node("a", "v1")])
    before = [r[:] for r in ws.grid]
    sync.reconcile_api(ws, sync.NODE_COLUMNS, [0],
                       {"a": node("a", "v2"), "z": node("z")}, True, False, "_data")
    assert ws.grid == before and ws.appended == [] and ws.n_clear == 0 and ss.requests == []


def test_api_rebuild_clears_then_repopulates():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    populate(ws, sync.NODE_COLUMNS, [node("old")])
    sync.reconcile_api(ws, sync.NODE_COLUMNS, [0], {"a": node("a")}, False, True, "_data")
    assert ws.n_clear == 1
    assert set(ids_in(ws, [0], NHASH, NCOLS)) == {"a"}


def test_api_delete_requests_descending():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    rows = [node(f"n{i}") for i in range(5)]   # rows 2..6
    populate(ws, sync.NODE_COLUMNS, rows)
    desired = {"n0": rows[0], "n2": rows[2]}   # n1,n3,n4 삭제
    sync.reconcile_api(ws, sync.NODE_COLUMNS, [0], desired, False, False, "_data")
    dels = [r["deleteDimension"]["range"]["startIndex"]
            for body in ss.requests for r in body.get("requests", [])
            if "deleteDimension" in r]
    assert dels == sorted(dels, reverse=True)  # 내림차순(인덱스 안 깨짐)
    assert set(ids_in(ws, [0], NHASH, NCOLS)) == {"n0", "n2"}


# ── reconcile_overwrite ─────────────────────────────────────────────────────
def test_overwrite_clears_and_writes_all():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    populate(ws, sync.NODE_COLUMNS, [node("j1"), node("j2"), node("j3")])
    sync.reconcile_overwrite(ws, sync.NODE_COLUMNS, {"a": node("a"), "b": node("b")},
                             False, "_data")
    assert ws.n_clear == 1
    header, idx = sync.read_sheet(ws, [0], NHASH, NCOLS)
    assert header == sync.NODE_COLUMNS and set(idx) == {"a", "b"}
    assert NHASH in ws.hidden_cols


def test_overwrite_then_api_is_noop():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    desired = {"a": node("a"), "b": node("b")}
    sync.reconcile_overwrite(ws, sync.NODE_COLUMNS, desired, False, "_data")
    ss.requests.clear()
    sync.reconcile_api(ws, sync.NODE_COLUMNS, [0], desired, False, False, "_data")
    assert ss.requests == [] and ws.appended == []   # overwrite 후 api는 변경 없음


def test_overwrite_dry_run_writes_nothing():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    populate(ws, sync.NODE_COLUMNS, [node("a")])
    before = [r[:] for r in ws.grid]
    sync.reconcile_overwrite(ws, sync.NODE_COLUMNS, {"x": node("x")}, True, "_data")
    assert ws.grid == before and ws.n_clear == 0


# ── push_meta ───────────────────────────────────────────────────────────────
def test_push_meta_writes_csv(tmp_path):
    ss = FakeSpreadsheet()
    p = tmp_path / "_meta.csv"
    p.write_text("섹션,키,값,설명\n개요,제목,X,\n", encoding="utf-8")
    sync.push_meta(ss, p, False, "_meta")
    ws = ss.worksheet("_meta")
    assert ws.grid[0] == ["섹션", "키", "값", "설명"]
    assert ws.grid[1] == ["개요", "제목", "X", ""]


def test_push_meta_missing_file_noop(tmp_path):
    ss = FakeSpreadsheet()
    sync.push_meta(ss, tmp_path / "nope.csv", False, "_meta")
    with pytest.raises(Exception):
        ss.worksheet("_meta")


def test_push_meta_dry_run_noop(tmp_path):
    ss = FakeSpreadsheet()
    p = tmp_path / "_meta.csv"; p.write_text("a,b\n1,2\n", encoding="utf-8")
    sync.push_meta(ss, p, True, "_meta")
    with pytest.raises(Exception):
        ss.worksheet("_meta")


# ── get_or_create_ws / _hide_hash_col ───────────────────────────────────────
def test_get_or_create_ws():
    ss = FakeSpreadsheet(); existing = ss.add_worksheet("_data", 100, 5)
    assert sync.get_or_create_ws(ss, "_data", 5) is existing
    new = sync.get_or_create_ws(ss, "_edges", ECOLS)
    assert new.title == "_edges" and ss.worksheet("_edges") is new


def test_hide_hash_request_shape():
    ss = FakeSpreadsheet(); ws = ss.add_worksheet("_data", 100, NCOLS)
    sync._hide_hash_col(ws, NHASH)
    rg = ss.requests[-1]["requests"][0]["updateDimensionProperties"]
    assert rg["range"]["dimension"] == "COLUMNS"
    assert rg["range"]["startIndex"] == NHASH and rg["range"]["endIndex"] == NHASH + 1
    assert rg["properties"]["hiddenByUser"] is True
    assert NHASH in ws.hidden_cols


# ── sync() 엔드투엔드 (open_spreadsheet 모킹) ────────────────────────────────
NODE_A = """---
id: fact-a
type: fact
title: A
summary: sa
tags: [x, y]
edges:
  - {target: fact-b, type: supports, weight: 0.5, note: ab}
---
body a
"""
NODE_B = """---
id: fact-b
type: fact
title: B
summary: sb
---
body b
"""


def test_sync_end_to_end_roundtrip(tmp_path, monkeypatch):
    vault = tmp_path / "vault"; (vault / "facts").mkdir(parents=True)
    (vault / "facts" / "fact-a.md").write_text(NODE_A, encoding="utf-8")
    (vault / "facts" / "fact-b.md").write_text(NODE_B, encoding="utf-8")
    csvdir = tmp_path / "sheet"; csvdir.mkdir()
    (csvdir / "_meta.csv").write_text("section,key,value\noverview,title,IB\n", encoding="utf-8")

    ss = FakeSpreadsheet()
    monkeypatch.setattr(sync, "open_spreadsheet", lambda: ss)

    sync.sync(vault, dry_run=False, rebuild=False, method="api", csv_dir=csvdir)

    # CSV 산출물
    assert (csvdir / "_data.csv").exists() and (csvdir / "_edges.csv").exists()
    data_rows = sync.read_csv_rows(csvdir / "_data.csv")
    assert data_rows[0] == sync.NODE_COLUMNS[:-1]
    # 시트 3탭
    dws, ews, mws = ss.worksheet("_data"), ss.worksheet("_edges"), ss.worksheet("_meta")
    assert set(ids_in(dws, [0], NHASH, NCOLS)) == {"fact-a", "fact-b"}
    assert len(ids_in(ews, [0, 1, 2], EHASH, ECOLS)) == 1     # a→b 엣지 1개
    assert mws.grid[0] == ["section", "key", "value"]

    # 2차 실행 → no-op(시트 변화 없음, clear/추가 없음)
    before = [r[:] for r in dws.grid]
    ss.requests.clear(); dws.appended.clear()   # run1의 누적 기록 리셋
    sync.sync(vault, dry_run=False, rebuild=False, method="api", csv_dir=csvdir)
    assert dws.grid == before and dws.n_clear == 0 and dws.appended == []


def test_sync_overwrite_method(tmp_path, monkeypatch):
    vault = tmp_path / "v"; (vault / "facts").mkdir(parents=True)
    (vault / "facts" / "fact-a.md").write_text(NODE_A, encoding="utf-8")
    (vault / "facts" / "fact-b.md").write_text(NODE_B, encoding="utf-8")
    csvdir = tmp_path / "sheet"
    ss = FakeSpreadsheet()
    monkeypatch.setattr(sync, "open_spreadsheet", lambda: ss)
    sync.sync(vault, dry_run=False, rebuild=False, method="overwrite", csv_dir=csvdir)
    dws = ss.worksheet("_data")
    assert dws.n_clear == 1
    assert set(ids_in(dws, [0], NHASH, NCOLS)) == {"fact-a", "fact-b"}
