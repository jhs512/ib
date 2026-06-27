"""네트워크 없이 gspread 워크시트/스프레드시트를 흉내내는 페이크.

그리드(2D 리스트)를 실제처럼 유지해서 write→read 라운드트립이 충실히 동작한다:
batch_get(범위 슬라이스), update/batch_update(블록 덮어쓰기), append_rows(말미 추가),
clear, spreadsheet.batch_update(deleteDimension=행 삭제, updateDimensionProperties=숨김 기록).
"""
from __future__ import annotations

import re

try:
    import gspread
    WorksheetNotFound = gspread.WorksheetNotFound
except Exception:  # gspread 미설치 환경 대비
    class WorksheetNotFound(Exception):
        pass


def parse_range(rng: str):
    """'A1:Q1' / 'A2:A' / 'Q2:Q' / 'A1' → (r0, r1|None, c0, c1|None) 0-based, end exclusive."""
    m = re.match(r"^([A-Z]+)(\d+)?(?::([A-Z]+)(\d+)?)?$", rng)
    if not m:
        raise ValueError(f"bad range: {rng}")
    col1, row1, col2, row2 = m.groups()

    def cidx(c):
        idx = 0
        for ch in c:
            idx = idx * 26 + (ord(ch) - 64)
        return idx - 1

    c0 = cidx(col1)
    r0 = int(row1) - 1 if row1 else 0
    if col2:
        c1 = cidx(col2) + 1
        r1 = int(row2) if row2 else None
    else:
        c1 = c0 + 1
        r1 = int(row1) if row1 else None
    return r0, r1, c0, c1


class FakeSpreadsheet:
    def __init__(self):
        self._by_title: dict[str, "FakeWorksheet"] = {}
        self._next_id = 1
        self.requests: list[dict] = []  # 기록된 batch_update 바디

    def worksheet(self, title):
        if title in self._by_title:
            return self._by_title[title]
        raise WorksheetNotFound(title)

    def add_worksheet(self, title, rows, cols):
        ws = FakeWorksheet(title, self._next_id, self)
        self._next_id += 1
        self._by_title[title] = ws
        return ws

    def _ws_by_id(self, sid):
        for ws in self._by_title.values():
            if ws.id == sid:
                return ws
        return None

    def batch_update(self, body):
        self.requests.append(body)
        for req in body.get("requests", []):
            if "deleteDimension" in req:
                rg = req["deleteDimension"]["range"]
                ws = self._ws_by_id(rg["sheetId"])
                if ws and rg.get("dimension") == "ROWS":
                    del ws.grid[rg["startIndex"]:rg["endIndex"]]
            elif "updateDimensionProperties" in req:
                rg = req["updateDimensionProperties"]["range"]
                ws = self._ws_by_id(rg["sheetId"])
                if ws:
                    ws.hidden_cols.add(rg["startIndex"])


class FakeWorksheet:
    def __init__(self, title, sid, spreadsheet, grid=None):
        self.title = title
        self.id = sid
        self.spreadsheet = spreadsheet
        self.grid: list[list[str]] = [list(r) for r in (grid or [])]
        self.hidden_cols: set[int] = set()
        self.n_clear = 0
        self.appended: list[list] = []
        spreadsheet._by_title.setdefault(title, self)

    # ── 내부 ──
    def _ensure(self, r, c):
        while len(self.grid) <= r:
            self.grid.append([])
        row = self.grid[r]
        while len(row) <= c:
            row.append("")

    def _write_block(self, start_row, start_col, values):
        for i, vrow in enumerate(values):
            for j, val in enumerate(vrow):
                self._ensure(start_row + i, start_col + j)
                self.grid[start_row + i][start_col + j] = "" if val is None else str(val)

    # ── gspread 유사 API ──
    def batch_get(self, ranges):
        out = []
        for rng in ranges:
            r0, r1, c0, c1 = parse_range(rng)
            rows = self.grid[r0:r1] if r1 is not None else self.grid[r0:]
            sl = []
            for row in rows:
                cc = row[c0:c1] if c1 is not None else row[c0:]
                sl.append(["" if x is None else x for x in cc])
            while sl and all(x == "" for x in sl[-1]):  # Sheets는 후행 빈 행 생략
                sl.pop()
            out.append(sl)
        return out

    def clear(self):
        self.n_clear += 1
        self.grid = []

    def update(self, range_name=None, values=None, value_input_option=None):
        r0, _, c0, _ = parse_range(range_name)
        self._write_block(r0, c0, values)

    def batch_update(self, data, value_input_option=None):
        for item in data:
            r0, _, c0, _ = parse_range(item["range"])
            self._write_block(r0, c0, item["values"])

    def append_rows(self, rows, value_input_option=None):
        self.appended.extend(rows)
        self._write_block(len(self.grid), 0, rows)
