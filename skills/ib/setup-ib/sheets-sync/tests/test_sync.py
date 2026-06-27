"""sync.py 순수 로직 테스트 (네트워크/Google API 불필요).

실행: pytest skills/ib/setup-ib/sheets-sync/tests/ -q
필요: PyYAML (sync가 사용). gspread는 I/O 함수에서만 import 되므로 불필요.
"""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # sheets-sync 디렉터리
import sync  # noqa: E402


NODE_MD = """---
id: fact-foo
title: Foo Fact
type: fact
namespace: demo
visibility: public
summary: A foo summary.
auto_inject: false
applicable_when: Empty
confidence: 0.9
verified_at: Empty
verified_by: Empty
staleness_signal: when foo changes
tags: [a, b, c]
related: [bar, baz]
edges:
  - {target: pillar-x, type: supports, weight: 0.8, note: "because"}
  - {target: fact-y, type: related_to, weight: 0.3, note: "loose"}
source_url: Empty
---

Body line one.
Body line two, with a comma.
"""


def write(p: Path, text: str) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


# ── parse_node ─────────────────────────────────────────────────────────────
def test_parse_node_valid(tmp_path):
    fm = sync.parse_node(write(tmp_path / "n.md", NODE_MD))
    assert fm["id"] == "fact-foo" and fm["type"] == "fact"
    assert "Body line one." in fm["__body__"]


def test_parse_node_not_a_node(tmp_path):
    assert sync.parse_node(write(tmp_path / "x.md", "no frontmatter")) is None


def test_parse_node_missing_id_or_type(tmp_path):
    assert sync.parse_node(write(tmp_path / "x.md", "---\ntype: fact\n---\nb")) is None
    assert sync.parse_node(write(tmp_path / "y.md", "---\nid: a\n---\nb")) is None


# ── node_row / _node_cell (JSON 없음 보장) ──────────────────────────────────
def test_node_row_no_json_lists(tmp_path):
    d = dict(zip(sync.NODE_COLUMNS, sync.node_row(sync.parse_node(write(tmp_path / "n.md", NODE_MD)))))
    assert d["tags"] == "a, b, c" and "[" not in d["tags"]   # 쉼표 구분, JSON 아님
    assert d["related"] == "bar, baz"
    assert d["auto_inject"] == "FALSE"
    assert d["confidence"] == "0.9"
    assert "Body line two, with a comma." in d["body"]


def test_node_row_hash_last(tmp_path):
    row = sync.node_row(sync.parse_node(write(tmp_path / "n.md", NODE_MD)))
    assert len(row) == len(sync.NODE_COLUMNS) and len(row[-1]) == 16


# ── content_hash ───────────────────────────────────────────────────────────
def test_content_hash_deterministic():
    assert sync.content_hash(["a", "b"]) == sync.content_hash(["a", "b"])


def test_content_hash_ignores_trailing_whitespace():
    assert sync.content_hash(["a ", "b\n"]) == sync.content_hash(["a", "b"])


def test_content_hash_changes_with_content():
    assert sync.content_hash(["a"]) != sync.content_hash(["b"])


# ── edge_rows ──────────────────────────────────────────────────────────────
def test_edge_rows(tmp_path):
    rows = sync.edge_rows(sync.parse_node(write(tmp_path / "n.md", NODE_MD)))
    assert len(rows) == 2
    assert rows[0][:4] == ["fact-foo", "supports", "pillar-x", "0.8"]
    assert len(rows[0]) == len(sync.EDGE_COLUMNS)


def test_edge_rows_skips_targetless(tmp_path):
    md = """---
id: n1
type: fact
edges:
  - {type: supports, note: no-target}
---
body"""
    assert sync.edge_rows(sync.parse_node(write(tmp_path / "n.md", md))) == []


# ── scan_vault ─────────────────────────────────────────────────────────────
def test_scan_vault_skips_and_collects(tmp_path):
    write(tmp_path / "facts" / "fact-foo.md", NODE_MD)
    write(tmp_path / "_system" / "AGENTS.md", "---\nid: sysnode\ntype: fact\n---\nb")
    write(tmp_path / "raw" / "r.md", NODE_MD.replace("fact-foo", "fact-raw"))
    write(tmp_path / "notes" / "plain.md", "not a node")
    nodes, edges = sync.scan_vault(tmp_path)
    assert set(nodes) == {"fact-foo"}        # skipped dirs + non-nodes excluded
    assert len(edges) == 2


def test_scan_vault_duplicate_id_raises(tmp_path):
    write(tmp_path / "a.md", NODE_MD)
    write(tmp_path / "b.md", NODE_MD)
    with pytest.raises(ValueError):
        sync.scan_vault(tmp_path)


# ── build_csvs round-trip ──────────────────────────────────────────────────
def test_build_csvs_roundtrip(tmp_path):
    write(tmp_path / "n.md", NODE_MD)
    nodes, edges = sync.scan_vault(tmp_path)
    out = tmp_path / "sheet"
    sync.build_csvs(nodes, edges, out)

    data = sync.read_csv_rows(out / "_data.csv")
    assert data[0] == sync.NODE_COLUMNS[:-1]          # 헤더에 _hash 없음
    rowd = dict(zip(data[0], data[1]))
    assert rowd["tags"] == "a, b, c"
    assert "Body line two, with a comma." in rowd["body"]   # 쉼표+줄바꿈 보존

    edge = sync.read_csv_rows(out / "_edges.csv")
    assert edge[0] == sync.EDGE_COLUMNS[:-1]
    assert len(edge) == 1 + 2                          # 헤더 + 엣지 2


# ── plan_changes (순수 diff) ────────────────────────────────────────────────
HI = len(sync.NODE_COLUMNS) - 1  # hash index


def _row(_id, h):
    r = [""] * len(sync.NODE_COLUMNS)
    r[0], r[-1] = _id, h
    return r


def test_plan_add():
    add, upd, dele, unch = sync.plan_changes({"a": _row("a", "h1")}, {}, True, HI)
    assert len(add) == 1 and not upd and not dele and unch == 0


def test_plan_unchanged():
    add, upd, dele, unch = sync.plan_changes({"a": _row("a", "h1")}, {"a": (2, "h1")}, True, HI)
    assert not add and not upd and not dele and unch == 1


def test_plan_update_on_hash_change():
    add, upd, dele, unch = sync.plan_changes({"a": _row("a", "h2")}, {"a": (2, "h1")}, True, HI)
    assert len(upd) == 1 and upd[0][0] == 2


def test_plan_delete():
    add, upd, dele, unch = sync.plan_changes({}, {"a": (2, "h1")}, True, HI)
    assert dele == [2] and not add and not upd


def test_plan_header_mismatch_forces_full_update():
    add, upd, dele, unch = sync.plan_changes({"a": _row("a", "h1")}, {"a": (2, "h1")}, False, HI)
    assert len(upd) == 1 and unch == 0
