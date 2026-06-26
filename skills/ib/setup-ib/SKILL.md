---
name: setup-ib
description: Sets up the Infinite Brain vault operating context in a repo or folder — writes an `## Infinite Brain vault` block (operating rules + ib skills table + node/edge quick reference) into CLAUDE.md/AGENTS.md and ensures the `_system/` scaffolding exists, so the ib skills know this directory is a knowledge-graph vault. Run once before first use of `init-vault`, `convert-note`, `query-vault`, `organize-vault`, or `vault-health` — or if those skills appear to be missing vault context (taxonomy, namespace, `_system/` entry points). Can also wire an (off-by-default) Google Sheets mirror — a hash-based one-way sync of the vault to a spreadsheet via GitHub Actions.
disable-model-invocation: true
---

# Setup Infinite Brain (ib) skills

Scaffold the per-vault configuration that the **ib** skills assume:

- **Operating block** — an `## Infinite Brain vault` section in `CLAUDE.md` (or `AGENTS.md`) so every agent knows this directory is a typed-node / typed-edge knowledge graph, and which `/`-commands operate on it.
- **`_system/` entry points** — `AGENTS.md` (taxonomy, visibility model, frontmatter schema, prohibited actions) and `INDEX.md` (the master node index every new node must update).
- **Defaults** — the starting namespace, the default node visibility, and the document language.

This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm with the user, then write. Reference: [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain).

This skill is the entry point for setting up ib in any directory — fresh or existing. `/init-vault` is the pure scaffolder it delegates to for stamping out the folder structure; don't point users at `/init-vault` directly for setup.

## Process

### 1. Explore

Look at the current directory to understand its starting state. Read whatever exists; don't assume:

- `CLAUDE.md` and `AGENTS.md` at the root — does either exist? Is there already an `## Infinite Brain vault` (or `## Agent skills`) section?
- `_system/` — does it exist? Which files are present (`AGENTS.md`, `INDEX.md`, `NODE-TYPES.md`, `EDGE-TYPES.md`, `FRONTMATTER-SCHEMA.md`)?
- Node-type folders at the root (`pillars/`, `decisions/`, `concepts/`, … `raw/`) — is this already a scaffolded vault, a partial one, or a plain repo?
- `_templates/Template - Infinite Node.md` — has a vault template been created?
- `git remote -v` — is this a code repo that *also* wants a vault, vs. a dedicated vault directory?

Classify the directory as one of: **(a) already a complete vault**, **(b) partial** (some `_system/` or folders), or **(c) not a vault yet**.

### 2. Present findings and ask

Summarise what's present and what's missing. Then walk the user through the decisions **one at a time** — present a section, get the answer, move to the next. Don't dump them all at once.

Assume the user may not know these terms. Each section opens with a short explainer (what it is, why the ib skills need it, what changes with a different choice), then the choices and the default.

**Section A — Vault location & scaffolding.**

> Explainer: The ib skills read and write typed nodes under folders like `pillars/`, `decisions/`, `concepts/`, and a `_system/` directory that holds the taxonomy and the master index. They need a place that *is* the vault. In a dedicated vault directory that's the root; in an existing code repo you usually don't want 17 node folders at the root, so the vault lives in a subfolder.

- **Root** — this directory is the vault. Best for a dedicated vault repo. (Default if no `src/`, `package.json`, etc. is present.)
- **Subfolder** (e.g. `vault/` or `brain/`) — the vault lives in a subfolder of an existing project. Ask for the folder name.

Then, based on the classification from step 1:
- If **not a vault yet** or **partial**, offer to run `/init-vault` in the chosen location to scaffold the full structure (17 folders, `_system/` files, template, two example nodes). If the user declines, seed only the minimum: `_system/AGENTS.md` and `_system/INDEX.md`.
- If **already complete**, skip scaffolding — only the CLAUDE.md block and defaults need writing.

**Section B — Namespace.**

> Explainer: Every node carries a `namespace` (e.g. `personal`, `work`, `research`) that groups it under a top-level area. The vault can hold several namespaces, but the skills need a default to stamp on new nodes when you don't specify one.

Default: `personal`. Ask the user for their starting namespace.

**Section C — Default visibility.**

> Explainer: Every node carries a `visibility` — `public` (safe across namespaces and general answers), `namespace` (used only when the task matches the node's namespace), `private` (used only when the human explicitly asks for that private context), or `system` (agent-facing operating rules, never presented as user content). The skills apply this default to new nodes.

Default: `public` (use `namespace` if the vault will mix several areas — upstream recommends `namespace` when unsure). Confirm or override.

**Section D — Document language.**

> Explainer: This sets the language the skills write **human-readable node content** in — titles, summaries, body prose, edge `note` fields, and the text of query answers and health reports. It does **not** change the vault's structural vocabulary: frontmatter field keys (`id`, `title`, `type`, …), the 17 node types, the 10 edge types, the visibility values (`public`/`namespace`/`private`/`system`), `id` slugs, namespace names, tags, folder names, and skill/command names always stay in their canonical English form so cross-references, file paths, and the taxonomy remain stable. Choosing a non-English language means everything *except* that fixed terminology is written in the chosen language.

Default: `English`. Ask the user which language node content should be written in (e.g. `English`, `한국어 (Korean)`). Record the answer as the document language.

**Section E — Google Sheets mirror (optional).**

> Explainer: Optionally mirror the vault to a Google Sheet — a tabular **read view** (one row per node: the 16 frontmatter fields + `body` + a hidden `_hash`). The markdown stays the source of truth; a GitHub Action re-syncs **only changed nodes** on push (content-hash based, no cache file — the baseline hash lives in the sheet's hidden `_hash` column). Useful for filtering/aggregation/dashboards and sharing with non-technical viewers. Requires a Google Cloud service account and a target spreadsheet, and the vault being a GitHub repo.

Default: **skip**. If the user opts in, carry out step 5 (Google Sheets mirror) after writing the vault context. Templates and the full rationale: [sheets-sync/](./sheets-sync/), [sheets-sync/README.md](./sheets-sync/README.md).

### 3. Confirm and edit

Show the user a draft of:

- The `## Infinite Brain vault` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited (see step 4), with `<namespace>`, `<visibility>`, and `<language>` filled in.
- The list of `_system/` files that will be created (if any), or "already present — leaving as-is".

Let them edit before writing.

### 4. Write

**Pick the file to edit:**

- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask the user which one to create — don't pick for them.

Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa) — always edit the one that's already there. If an `## Infinite Brain vault` block already exists in the chosen file, update its contents in place rather than appending a duplicate. Don't overwrite the user's edits to surrounding sections.

Write the block using the seed in this skill folder as a starting point — [vault-claude-block.md](./vault-claude-block.md) — substituting the namespace, visibility, and document language from Section B/C/D. When the vault lives in a subfolder, note the path in the block's first line ("The `vault/` directory is an AI-first knowledge-graph vault…").

Then ensure the `_system/` entry points exist:

- If the user opted into `/init-vault`, invoke it in the chosen location, passing along the namespace from Section B and the document language from Section D so it doesn't re-ask, and skip its operating-block step — the CLAUDE.md/AGENTS.md block is this skill's job and was just written above.
- Otherwise seed the minimum so the other ib skills have something to read: `_system/AGENTS.md` and `_system/INDEX.md` (empty per-type tables). For `AGENTS.md`, copy the seed in this skill folder — [vault-agents-template.md](./vault-agents-template.md) — substituting `<namespace>` from Section B and `<language>` from Section D; it carries the full operating rules (taxonomy, visibility model, frontmatter schema, document-language rule, log-writing rules, prohibited actions, first-session protocol). Leave any existing `_system/` file untouched.

### 5. Google Sheets mirror (optional)

Only if the user opted in at Section E. The markdown vault stays the source of truth; the sheet is a generated view synced by GitHub Actions. Templates: [sheets-sync/](./sheets-sync/); rationale (incl. why there is no cache file and how it stays correct in stateless CI): [sheets-sync/README.md](./sheets-sync/README.md).

Prerequisites: the vault is a GitHub repo and `gh` is authenticated with `repo` + `workflow` scope.

**5a. Browser automation is required — check it's on first.** Creating the spreadsheet (5b) and the GCP console setup (5d) are done by driving a browser. Before going further, confirm a browser-driving tool is actually available to you — e.g. the `claude-in-chrome` skill or a Chrome/DevTools MCP. **Do not assume or fake clicks.**
- **Available** → proceed; you'll drive the console in 5b/5d, pausing only for the human-only clicks.
- **Not available** → **stop and tell the user to turn on browser automation** (recommend the **Claude in Chrome** extension / a Chrome MCP). Be direct that doing the Google Cloud console steps by hand is painful and error-prone, so this skill needs browser-use enabled. Wait until it's on, then continue — don't limp through it manually.

**5b. Choose the target spreadsheet — new or existing.** Ask the user:
- **Create a new sheet** (e.g. titled `지식` / "Knowledge") — preferred for a fresh vault. Create it by driving the browser to `sheets.new` (or via a Google Drive/Sheets tool if one is available). Capture the **spreadsheet ID** from the URL (`https://docs.google.com/spreadsheets/d/<ID>/edit`).
- **Use an existing sheet** — ask for its URL or ID. If syncing into a specific tab rather than the first one, also capture the tab `gid` (the `#gid=<N>` / `?gid=<N>` in the URL) for `WORKSHEET_GID`.

Record `SPREADSHEET_ID` (and `WORKSHEET_GID` if set). The sync uses 18 columns (16 frontmatter fields + `body` + hidden `_hash`); an existing sheet's first tab will be reshaped to that header on first sync, so prefer a dedicated/empty tab.

**5c. Copy templates into the vault repo.**
- `sheets-sync/sync.py` → vault root `sync.py`
- `sheets-sync/requirements.txt` → vault root `requirements.txt` (merge if one already exists)
- `sheets-sync/sheets-sync.yml` → `.github/workflows/sheets-sync.yml`
- Ensure `.gitignore` contains `*.json` (service-account keys must never be committed).
- If the vault lives in a subfolder, set `--vault <folder>` in the workflow's run step.

**5d. Create the Google Cloud service account.** Drive the browser through these, pausing for the human-only key download:
1. Create a GCP project (`console.cloud.google.com/projectcreate`), then switch to it.
2. Enable the **Google Sheets API** for the project.
3. Create a **service account**; record its `client_email` (e.g. `name@project.iam.gserviceaccount.com`).
4. Create a **JSON key** — ★ **the human clicks the final "Create" / accepts the download** (it is a credential download; never do it silently for them in any mode). Save the file *outside* the repo.

**5e. Share the spreadsheet with the service account — ★ human only.** This is a permission change, so the user must do it themselves. Guide them explicitly:
1. Open the target spreadsheet (from 5b).
2. Click **Share** (top-right).
3. Paste the service-account `client_email` from 5d.
4. Set the role to **Editor**, untick "Notify people" if shown, and **Send / Share**.
Without this the sync fails with `403 PERMISSION_DENIED`. Confirm with the user that they've done it before continuing.

**5f. Wire the repo via `gh`.**
- `gh secret set GOOGLE_SA_KEY < /path/to/key.json` (uploaded encrypted; never printed or committed).
- `gh variable set SPREADSHEET_ID --body <spreadsheet-id>` (and `gh variable set WORKSHEET_GID --body <gid>` if a specific tab).

**5g. Initial sync + push.**
- Verify locally first: `SPREADSHEET_ID=… GOOGLE_APPLICATION_CREDENTIALS=…/key.json python sync.py --vault <vault> --dry-run`, then run without `--dry-run`.
- Commit the templates and push → the **Sheets Sync** Action reflects only changed nodes on every subsequent push.

Report what was created (project id, service-account email, spreadsheet URL, secret/variable names) and remind the user the key file is a live credential to keep safe (or rotate later in GCP).

### 6. Done

Tell the user setup is complete and which ib skills now have the context they need (`init-vault`, `convert-note`, `query-vault`, `organize-vault`, `vault-health`). If the Google Sheets mirror was wired, note that pushes now auto-sync changed nodes to the sheet. Mention they can edit the `## Infinite Brain vault` block or `_system/*.md` directly later — re-running this skill is only needed to change the namespace/visibility/language defaults, relocate the vault, or set up the sheets mirror.
