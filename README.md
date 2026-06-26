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
| `/setup-ib` | Wire the vault operating context into any repo/folder (run once, first) — optionally sets up a Google Sheets mirror |
| `/init-vault` | Scaffold a complete vault — 17 folders, system schema, templates, example nodes (usually invoked for you by `/setup-ib`) |
| `/convert-note` | Decompose raw material (`raw/`) into atomic typed nodes |
| `/query-vault` | Answer questions via graph traversal — token-cheap scoped retrieval |
| `/organize-vault` | Interactive audit: orphans, contradictions, confidence gaps, taxonomy drift |
| `/vault-health` | Automated maintenance: confidence decay + full audit + health report (`auto` mode for cron) |

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
- **Minimal API calls.** One read + one `batch_update` / `append_rows` / `deleteDimension` per tab.

### Setup (via `/setup-ib`)

`/setup-ib` wires the whole thing end-to-end:

1. Create a new spreadsheet (or point at an existing one).
2. Drive the browser to create a Google Cloud project, enable the Sheets API, and a service account. **★ you click the JSON-key download** (it's a credential).
3. **★ you share the spreadsheet** with the service-account email as **Editor** (a permission change only you can make; without it the API returns 403).
4. It sets the encrypted `GOOGLE_SA_KEY` secret + `SPREADSHEET_ID` variable and copies `sync.py` + the workflow into the repo.
5. Push → the **Sheets Sync** Action reflects changed nodes/edges automatically.

> Browser automation (e.g. Claude in Chrome) is required for the console steps — `/setup-ib` will tell you to enable it if it's missing, rather than walking you through the console by hand.

### Run modes

```bash
python sync.py --vault .            # incremental (default) — only changed rows
python sync.py --vault . --dry-run  # preview the plan, write nothing
python sync.py --vault . --rebuild  # wipe the tabs and regenerate from markdown
```

Templates and full rationale: [`skills/ib/setup-ib/sheets-sync/`](skills/ib/setup-ib/sheets-sync/).

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
    ├── setup-ib/        #   onboarding + agent-rules seed
    ├── init-vault/      #   scaffolder + vendored system templates
    ├── convert-note/    #   raw → atomic nodes
    ├── query-vault/     #   scoped graph retrieval
    ├── organize-vault/  #   interactive audit
    └── vault-health/    #   decay + audit + report (cron-ready)
.claude-plugin/
    ├── plugin.json      # Claude Code plugin manifest
    └── marketplace.json # marketplace listing
```

Adding a new skill: create `skills/<group>/<name>/SKILL.md` with `name` + `description` frontmatter, register the group in `.claude-plugin/plugin.json`.

## Credits & License

Built on the Infinite Brain methodology by [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain), inspired by [AI Impact — How to Build an Infinite Brain with AI](https://www.youtube.com/watch?v=z02Y-1OvWSM).

[MIT](LICENSE)
