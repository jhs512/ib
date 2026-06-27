<p align="center">
  <img src="https://img.shields.io/badge/Version-0.3.0-brightgreen.svg" alt="Version">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-purple.svg" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/Skills-6-orange.svg" alt="6 Skills">
  <img src="https://img.shields.io/badge/Vault-Obsidian_Compatible-7c3aed.svg" alt="Obsidian Compatible">
  <a href="https://github.com/jhs512/ib/stargazers"><img src="https://img.shields.io/github/stars/jhs512/ib?style=social" alt="GitHub Stars"></a>
</p>

# Infinite Brain — permanent, typed memory for your AI agent

**English** | [한국어](README_KO.md)

> AI agents forget everything between sessions. **Infinite Brain** turns any folder into a typed knowledge graph your agent can build, maintain, and query — every note a typed **node**, every connection a typed **edge**, with confidence scores that decay until re-verified. Obsidian-compatible, plain markdown, no database.

## Why a graph, not a pile of notes?

Long, loosely-linked documents are fine for humans but broken for agents: they read too much, links don't say *why* two notes connect, and metadata is too weak for reliable retrieval. Infinite Brain fixes this with:

- **16+1 node types** (`pillar`, `decision`, `fact`, `hypothesis`, `playbook`, …) — one idea per node, 50–300 words
- **10 edge types** (`supports`, `contradicts`, `derived_from`, `depends_on`, …) — every edge has a direction, weight, and a reason
- **Trust metadata** — `confidence` (0.0–1.0), `verified_at`, `staleness_signal`, `visibility` (`public`/`namespace`/`private`/`system`)
- **Scoped retrieval** — answer questions by traversing edges (~600 tokens), not by reading the whole vault (~9,000 tokens)
- **Audit trail** — every skill run writes a lightweight log node; weekly health checks decay stale confidence automatically

## The Skills

| Command | What it does |
|---|---|
| `/setup-ib` | Wire the vault operating context into any repo/folder (run once, first). Re-running offers a clean "reset and re-setup" (local-only) |
| `/init-vault` | Scaffold a complete vault — 17 folders, system schema, templates, example nodes (usually invoked for you by `/setup-ib`) |
| `/convert-note` | Decompose raw material (`raw/`) into atomic typed nodes |
| `/query-vault` | Answer questions via graph traversal — token-cheap scoped retrieval |
| `/organize-vault` | Interactive audit: orphans, contradictions, confidence gaps, taxonomy drift |
| `/vault-health` | Automated maintenance: confidence decay + full audit + health report (`auto` mode for cron) |
| `/setup-gcp` | *(optional, for the Sheets mirror)* Provision reusable Google Cloud credentials once — project (default `infinite-brain`), service account, JSON key; idempotent (reuses what exists) |
| `/setup-sheets-sync` | *(optional, for the Sheets mirror)* Connect the current vault to a Google Sheet (default `지식`) — create/share the sheet, copy templates, wire `gh`, initial sync |

## Google Sheets mirror (optional)

Beyond Obsidian, the vault can mirror itself to a **Google Sheet** — a live, Google-native **read view** of your knowledge graph. The markdown is always the source of truth; the sheet is a generated projection that's easy to filter, build dashboards on, share with non-technical people, or hand to a conversational agent (e.g. a Gemini app reading the sheet to talk *over* your graph).

```
markdown vault (truth) ──push──▶ GitHub Action ──▶ sync.py ──▶ Google Sheet (view)
  convert-note writes nodes         on *.md change   hash diff      _data · _edges
```

### What it syncs

Two tabs, normalized for graph traversal:

| Tab | One row per | Columns |
|---|---|---|
| `_data` | node | `id, title, type, namespace, visibility, summary, auto_inject, applicable_when, confidence, verified_at, verified_by, staleness_signal, tags, related, source_url, body` (+ hidden `_hash`) |
| `_edges` | relation | `source, type, target, weight, note` (+ hidden `_hash`) |

- `tags` / `related` are plain **comma-separated text** — no JSON inside cells.
- Relations live in `_edges`, derived automatically from each node's `edges:` frontmatter, so **both directions are one filter away**: outgoing = `source = X`, backlinks = `target = X`.
- A `_meta` tab (if present) documents the schema for humans/agents and is left untouched by sync.

### How sync stays cheap and correct

- **Incremental by content hash.** Each node/edge row is normalized and hashed; only rows whose hash changed are written. Adds/deletes are detected by key-set diff (node key = `id`, edge key = `source|type|target`).
- **No cache file.** The baseline hash lives in each tab's hidden `_hash` column, not a local file. GitHub Actions runners are ephemeral, so a local cache would vanish between runs — keeping state *in the sheet* makes it correct on stateless CI and **self-healing** if someone hand-edits the sheet.
- **Small, constant API calls.** Per tab: one `batch_get` that reads **only the `id` + `_hash` columns — never `body`** (the hash already encodes the body), plus one `batch_update` / `append_rows` / `deleteDimension` for the changes. Call count doesn't grow with row count, and the read payload barely does either.
- **Ceiling.** A spreadsheet isn't a graph DB — Google Sheets caps at 10M cells (~500K node rows). Past that, move to a real store; the markdown vault is unaffected.

### Setup (two skills: `/setup-gcp` once, then `/setup-sheets-sync` per vault)

The mirror is set up in two steps so the heavy Google Cloud work happens **once** and is reused across every vault:

**`/setup-gcp` — once per Google account (idempotent).**

1. Create or **reuse** a Google Cloud project (default `infinite-brain`) and enable the Sheets + Drive APIs. Prefers the `gcloud` CLI; falls back to driving the browser. It checks for an existing project/service account/key and reuses them — it will **not** create duplicate projects.
2. Create (or reuse) a service account and its JSON key. With `gcloud` the key is written for you; via the browser **★ you click the JSON-key download** (it's a credential). The result is saved to `~/.config/ib/sheets-sync.env` for reuse.

**`/setup-sheets-sync` — per vault.**

3. Create a new spreadsheet (default name `지식`, via the Google Drive tools) or point at an existing one.
4. **★ you share the spreadsheet** with the service-account email as **Editor** (a permission change only you can make; without it the API returns 403).
5. It sets the encrypted `GOOGLE_SA_KEY` secret + `SPREADSHEET_ID` variable and copies `sync.py` + the workflow into the repo.
6. Push → the **Sheets Sync** Action reflects changed nodes/edges automatically.

> If `gcloud` isn't installed, `/setup-gcp` falls back to browser automation (e.g. Claude in Chrome) for the console steps and will tell you to enable it if it's missing, rather than walking you through the console by hand.

### Git-tracked CSV snapshot

Every run also builds `sheet/_data.csv` + `sheet/_edges.csv` — a plain-text, diffable snapshot of the sheet committed to the repo (`sheet/_meta.csv` is the hand-maintained schema doc). So the spreadsheet's content is versioned in git too, and the Action commits the refreshed snapshot back.

### Run modes

```bash
python sync.py --vault .                     # api incremental (default) — only changed rows
python sync.py --vault . --dry-run           # preview the plan, write nothing
python sync.py --vault . --method overwrite  # clear each tab and rewrite in full
python sync.py --vault . --rebuild           # api mode: wipe the tabs and regenerate
```

Templates, tests, and full rationale: [`skills/ib/setup-sheets-sync/`](skills/ib/setup-sheets-sync/).

### Troubleshooting

| Symptom | Cause → fix |
|---|---|
| `403 PERMISSION_DENIED` | The sheet isn't shared with the service account → **Share** it with the `client_email` as **Editor**. |
| `SPREADSHEET_ID is required` | Set the `SPREADSHEET_ID` repo variable (or env var for local runs). |
| Sync wrote to / wiped the wrong tab | Tabs are matched **by name** (`_data` / `_edges`) and it never falls back to the first tab — keep those names or set `NODE_TAB` / `EDGE_TAB`. |
| "no changes" but you edited markdown | The file isn't a node (needs `id` + `type` frontmatter), or it lives under a skipped dir (`_system`, `_templates`, `raw`, …). |
| Rows look empty in the browser | A long `body` makes the row very tall — the data is there; scroll or check the formula bar (turn off text-wrap on the `body` column for a compact view). |
| Auth fails after working before | The `GOOGLE_SA_KEY` secret is malformed (must be the full JSON) or the key was revoked → rotate it (see FAQ). |
| Sheet looks out of sync / corrupted | Run `python sync.py --vault . --rebuild` to wipe and regenerate from markdown. |

### FAQ

- **Can I edit the sheet directly?** No — it's a generated view; manual edits are overwritten on the next sync (and rows not in the vault are deleted). Author in markdown.
- **Where do I add knowledge, then?** In the vault — e.g. drop material in `raw/` and run `/convert-note`.
- **Is my service-account key safe in a public repo?** Yes — it's stored as an encrypted GitHub **secret**, never committed (`*.json` is git-ignored); the key file stays on your machine.
- **How do I rotate the key?** In GCP, create a new JSON key for the service account, run `gh secret set GOOGLE_SA_KEY < new-key.json`, then delete the old key.
- **How does an agent use the sheet?** It reads `_data` (nodes) and `_edges` (relations) — `summary` for scanning, edges for traversal (`source=X` / `target=X`), `body` for depth.

## Install

### As a Claude Code plugin (marketplace)

```shell
/plugin marketplace add jhs512/ib
/plugin install infinite-brain@ib
```

### With the skills CLI (Claude Code · Codex · Cursor · OpenCode)

```bash
# everything
npx skills@latest add jhs512/ib --all

# or pick skills
npx skills@latest add jhs512/ib --skill init-vault --skill query-vault

# or target one agent
npx skills@latest add jhs512/ib -a claude-code
```

## Quickstart

```
1.  /setup-ib          # once — sets defaults, writes the operating block, and
                       # scaffolds the vault (runs /init-vault for you)
2.  Drop anything into raw/   (articles, meeting notes, transcripts — a
                               descriptive filename is enough)
3.  /convert-note      # raw file → atomic typed nodes, wired with edges
4.  /query-vault       # ask questions; the agent traverses the graph
5.  /schedule weekly /vault-health auto    # optional: self-maintaining memory
```

Open the same folder in Obsidian at any point — Graph View renders your agent's memory as a live node map.

## Copy-paste prompts

After installing, try these in Claude Code:

**Personal knowledge base**
```
/setup-ib — I want a personal vault. Namespace "personal", then init the vault
and convert everything currently in raw/.
```

**Team decision log**
```
/query-vault — why did we choose PostgreSQL over MongoDB? Trace the decision
back to its supporting evidence and tell me if anything contradicts it.
```

**Research ingestion**
```
I just dropped 5 papers into raw/. Run /convert-note on all of them, then
/organize-vault to find contradictions between the new nodes and what I
already believe.
```

**Memory hygiene**
```
/vault-health — decay anything I haven't verified in 90 days and give me the
top 5 things I should re-confirm or delete.
```

## How it relates to neighbors

| Repo | What it is | Relationship |
|---|---|---|
| [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain) | The original Infinite Brain vault template + methodology | **Upstream origin.** This repo packages the methodology as an installable plugin: self-contained `init-vault` (vendored system templates), a `setup-ib` onboarding skill, and multi-agent distribution via the skills CLI. |
| [Obsidian](https://obsidian.md/) + Dataview / Web Clipper | Human-facing vault browser and capture tools | **Complementary.** Agents write the graph; Obsidian renders it. No lock-in — it's all plain markdown. |
| Claude Code session memory / CLAUDE.md | Per-project agent instructions | **Different layer.** CLAUDE.md tells the agent *how to behave*; Infinite Brain stores *what it knows* — versionable, auditable, queryable. |

## Repo layout

```
skills/
└── ib/                  # Infinite Brain skill group
    ├── setup-ib/            #   onboarding + agent-rules seed
    ├── init-vault/          #   scaffolder + vendored system templates
    ├── setup-gcp/           #   (optional) reusable Google Cloud credentials for the Sheets mirror
    ├── setup-sheets-sync/   #   (optional) per-vault Sheets mirror wiring + sync templates/tests
    ├── convert-note/        #   raw → atomic nodes
    ├── query-vault/         #   scoped graph retrieval
    ├── organize-vault/      #   interactive audit
    └── vault-health/        #   decay + audit + report (cron-ready)
.claude-plugin/
    ├── plugin.json      # Claude Code plugin manifest
    └── marketplace.json # marketplace listing
```

Adding a new skill: create `skills/<group>/<name>/SKILL.md` with `name` + `description` frontmatter, register the group in `.claude-plugin/plugin.json`.

## Credits & License

Built on the Infinite Brain methodology by [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain), inspired by [AI Impact — How to Build an Infinite Brain with AI](https://www.youtube.com/watch?v=z02Y-1OvWSM).

[MIT](LICENSE)
