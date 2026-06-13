<!--
Seed template for the `## Infinite Brain vault` block that setup-ib writes into
CLAUDE.md (or AGENTS.md). Replace <namespace>, <visibility>, and <language> with
the user's answers. If the block already exists, update its contents in place —
do not append a duplicate.
-->

## Infinite Brain vault

This directory is an AI-first knowledge-graph vault. Every note is a typed **node**; every connection is a typed **edge**. Act as a Knowledge Architect, not a chat assistant.

Read `_system/AGENTS.md` before any vault operation — it defines the full node/edge taxonomy, visibility model, frontmatter schema, and prohibited actions.

### ib skills

| Command | When to use |
|---|---|
| `/init-vault` | Scaffold a fresh vault in a new directory |
| `/convert-note` | Decompose `raw/` files into typed atomic nodes |
| `/query-vault` | Answer questions via scoped graph traversal (token-cheap) |
| `/organize-vault` | Interactive audit of orphans, contradictions, confidence gaps |
| `/vault-health` | Confidence decay + full audit + health-report node |

### Quick reference

- Default namespace: `<namespace>`
- Default visibility: `<visibility>` (model: `public` | `namespace` | `private` | `system`)
- Document language: `<language>` — write all human-readable node content (titles, summaries, bodies, edge `note` fields, query answers, health reports) in this language. Keep the structural vocabulary in canonical English: frontmatter keys, the node/edge type names above, visibility values, `id` slugs, namespace names, tags, folder names, and skill/command names. See `_system/AGENTS.md` → Document Language.
- Node types: `pillar decision concept question playbook task event pattern hypothesis fact source bookmark note contact reference custom log`
- Edge types: `related_to depends_on derived_from contradicts supports part_of preceded_by followed_by authored_by tagged_with`
- Entry point for agents: `_system/INDEX.md` — every new node must update it
- Never leave `edges: []` empty on an established node
- `raw/` is immutable source material — never edit it; `/convert-note` moves processed originals to `raw/processed/`
- Every skill run writes a log node to `logs/` (reduced 8-field schema; never indexed, never edited)
