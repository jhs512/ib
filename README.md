<p align="center">
  <img src="https://img.shields.io/badge/Version-0.2.0-brightgreen.svg" alt="Version">
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
| `/setup-ib` | Wire the vault operating context into any repo/folder (run once, first) |
| `/init-vault` | Scaffold a complete vault — 17 folders, system schema, templates, example nodes (usually invoked for you by `/setup-ib`) |
| `/convert-note` | Decompose raw material (`raw/`) into atomic typed nodes |
| `/query-vault` | Answer questions via graph traversal — token-cheap scoped retrieval |
| `/organize-vault` | Interactive audit: orphans, contradictions, confidence gaps, taxonomy drift |
| `/vault-health` | Automated maintenance: confidence decay + full audit + health report (`auto` mode for cron) |

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
