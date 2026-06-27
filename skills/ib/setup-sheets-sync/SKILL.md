---
name: setup-sheets-sync
description: Wires the Google Sheets mirror for the current Infinite Brain vault — creates (by default) a Google Sheet named `지식`, shares it with the service account, copies the sync templates (sync.py, workflow, requirements, _meta) into the vault repo, sets the `gh` secret/variable, and runs the initial one-way sync. The markdown vault stays the source of truth; a GitHub Action re-syncs only changed nodes/edges on every push. Browser automation (e.g. Claude in Chrome) is a hard prerequisite — the skill checks it is enabled up front and STOPS if not. Requires the reusable Google Cloud credentials from `setup-gcp` (run that once first) and that the vault is a GitHub repo with `gh` authenticated. Defaults the spreadsheet to a new sheet titled `지식`; the user can reuse an existing sheet or pick another name.
disable-model-invocation: true
---

# Setup the Google Sheets mirror for this vault

This is the **per-vault** half of the Sheets mirror. The reusable, account-level credentials (GCP project, service account, JSON key) come from **`/setup-gcp`** — run that once first. This skill then connects *this* vault to a spreadsheet.

The markdown vault is the source of truth; the sheet is a generated **read view**. A GitHub Action re-syncs only changed nodes/edges on push (content-hash based, no cache file — the baseline hash lives in each tab's hidden `_hash` column). Rationale and the no-cache design: [README.md](./README.md).

## 0. Browser automation must be ON — check this FIRST (hard gate)

This skill assumes browser use. **Before doing anything else**, confirm a browser-driving tool is available and enabled — the `claude-in-chrome` skill or a Chrome/DevTools MCP.

- **Enabled** → continue to the prerequisites.
- **Not enabled** → **STOP immediately.** Tell the user to turn on browser automation (recommend the **Claude in Chrome** extension / a Chrome MCP) and re-run. Don't half-wire the mirror and fail at the sharing/console step.

(Sheet creation may go through the Google Drive tools without a browser, but the sharing step and any console/sheet interaction need browser-use, so it is required up front rather than discovered mid-run.)

## 1. Prerequisites

- **ib context exists** in this directory (run `/setup-ib` first if not).
- **GCP credentials exist.** Read `~/.config/ib/sheets-sync.env`. If it's missing or incomplete (`GCP_PROJECT_ID`, `SA_EMAIL`, `SA_KEY_PATH`), stop and tell the user to run **`/setup-gcp`** first (offer to invoke it). Load `SA_EMAIL` and `SA_KEY_PATH` from it.
- **GitHub repo + `gh`.** The vault is a GitHub repo and `gh` is authenticated with `repo` + `workflow` scope (`gh auth status`).

If the vault lives in a subfolder of a larger repo, note the vault folder — it becomes `--vault <folder>` in the workflow and local runs.

## 2. Choose the target spreadsheet (default: a new `지식` sheet)

The two tabs are managed **by name**: `_data` (nodes: 15 frontmatter fields + `body` + hidden `_hash`; `tags`/`related` are comma-separated, not JSON) and `_edges` (normalized relations `source | type | target | weight | note`, auto-generated from each node's `edges`). A `_meta` schema tab, if present, is left untouched. Tab names can be overridden later with `NODE_TAB`/`EDGE_TAB`.

Prefer the **Google Drive MCP tools** for the create/lookup. If they aren't available, drive the browser to `sheets.new` (browser-use is already confirmed on from §0).

1. **Look for an existing sheet first** (stay idempotent). Search Drive for a spreadsheet named `지식`:
   - `mcp__claude_ai_Google_Drive__search_files` for name `지식` (mimeType `application/vnd.google-apps.spreadsheet`).
   - If one (or more) is found, ask the user: **reuse it** (use its id) or **create a new one anyway**.
2. **Default — create a new sheet titled `지식`** ("Knowledge") if none exists or the user wants a fresh one:
   - `mcp__claude_ai_Google_Drive__create_file` with mimeType `application/vnd.google-apps.spreadsheet` and name `지식`.
   - The user may pick a **different name**, or supply an **existing sheet's URL/ID** to use instead.
3. **Capture `SPREADSHEET_ID`** from the file id / the URL (`https://docs.google.com/spreadsheets/d/<ID>/edit`).

## 3. Share the spreadsheet with the service account — ★ human only

The sync authenticates as the service account, so the sheet must grant it access. There is no Drive MCP tool to add a permission, and this is a permission change either way, so **the user does this themselves**:

1. Open the target spreadsheet.
2. Click **Share** (top-right).
3. Paste the `SA_EMAIL` from `~/.config/ib/sheets-sync.env`.
4. Set the role to **Editor**, untick "Notify people" if shown, and **Send / Share**.

Without this the sync fails with `403 PERMISSION_DENIED`. Confirm the user has done it before continuing.

## 4. Copy the sync templates into the vault repo

From this skill folder into the vault:

- [`sync.py`](./sync.py) → vault root `sync.py`
- [`requirements.txt`](./requirements.txt) → vault root `requirements.txt` (merge if one already exists)
- [`sheets-sync.yml`](./sheets-sync.yml) → `.github/workflows/sheets-sync.yml`
- [`_meta.csv`](./_meta.csv) → `sheet/_meta.csv` (the schema doc that fills the `_meta` tab; edit later if desired)
- [`tests/`](./tests/) → `tests/` (optional — the network-free unit tests)

Then:
- Ensure `.gitignore` contains `*.json` (service-account keys must never be committed).
- If the vault lives in a subfolder, set `--vault <folder>` in the workflow's run step.

Each sync builds `sheet/_data.csv` + `sheet/_edges.csv` (a git-tracked snapshot of the sheet); these get committed.

## 5. Wire the repo via `gh`

- `gh secret set GOOGLE_SA_KEY < "$SA_KEY_PATH"` (uploaded encrypted; never printed or committed).
- `gh variable set SPREADSHEET_ID --body <spreadsheet-id>` (tab names default to `_data`/`_edges`; set `NODE_TAB`/`EDGE_TAB` variables only to override).

## 6. Initial sync + push

- Verify locally first:
  ```bash
  SPREADSHEET_ID=… GOOGLE_APPLICATION_CREDENTIALS="$SA_KEY_PATH" python sync.py --vault <vault> --dry-run
  ```
  then run without `--dry-run` (default `--method api`; `--method overwrite` clears + rewrites each tab).
- Commit the templates **and the generated `sheet/*.csv` snapshot**, then push → the **Sheets Sync** Action reflects only changed nodes/edges on every subsequent push (and commits the refreshed CSV snapshot back).

## 7. Done

Report what was wired: the spreadsheet URL/id, the service-account email it's shared with, and the `gh` secret/variable names. Note that pushes now auto-sync changed nodes to the sheet. Remind the user the key file (`SA_KEY_PATH`) is a live credential to keep safe (or rotate later via `/setup-gcp`). Because the GCP credentials are reusable, setting up the mirror for *another* vault is just this skill again — no `/setup-gcp` needed.
