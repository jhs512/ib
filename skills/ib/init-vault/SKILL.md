---
name: init-vault
description: >
  Scaffold a fresh Infinite Brain vault from scratch in the current directory.
  Creates all folders, system files, template, and example nodes.
  Invoked with /init-vault.
allowed-tools: Read, Write, Glob
---

# Init Vault — Scaffold a Fresh Infinite Brain

You are creating a new Infinite Brain vault from scratch in the current directory.

This skill is a pure scaffolder: it stamps out the folder structure, `_system/` files, template, and example nodes. The entry point for setting up ib — whether in a fresh directory or an existing repo — is `/setup-ib`, which classifies the directory, decides the vault location, collects defaults, and invokes this skill as one of its steps.

## Steps

1. Determine the namespace and the document language. If they were already provided (e.g. this skill was invoked from `/setup-ib` with both decided), use them and don't re-ask. Otherwise ask: "What namespace should this vault start with? (e.g. 'personal', 'work', 'research')" and "Which language should node content be written in? (e.g. 'English', '한국어 (Korean)')". The document language sets the language of all human-readable node content (titles, summaries, bodies, edge notes); the structural vocabulary — frontmatter keys, node/edge type names, visibility values, `id` slugs, namespaces, tags, folder names — always stays in canonical English (see the Document Language section in `vault-agents-template.md`).
2. Create the 17 root folders:
   `pillars decisions concepts questions playbooks tasks events patterns hypotheses facts sources bookmarks notes contacts references custom raw _system _templates`
3. Create `.gitkeep` in each empty folder so git tracks them.
4. Create `_system/` files. **Do not write these from memory** — copy the reference templates bundled in this skill's `templates/` folder (paths relative to this SKILL.md):
   - `INDEX.md` ← `templates/INDEX.md` — master node index, one table per type. Replace the two example rows with the actual example-node IDs from step 7 and update the *Last updated* date.
   - `NODE-TYPES.md` ← `templates/NODE-TYPES.md` — definitions for all 16 content types
   - `EDGE-TYPES.md` ← `templates/EDGE-TYPES.md` — definitions for all 10 edge types
   - `FRONTMATTER-SCHEMA.md` ← `templates/FRONTMATTER-SCHEMA.md` — full field reference, including the reduced 8-field log schema
   - `LOCAL-TYPES.md` ← `templates/LOCAL-TYPES.md` — placeholder for custom types
   - `WORKFLOWS.md` ← `templates/WORKFLOWS.md` — when each skill runs, scheduling recommendations (weekly `/vault-health auto`), GitHub Actions example
   - `AGENTS.md` — agent operating rules. Copy the seed from the setup-ib skill folder (`../setup-ib/vault-agents-template.md`), substituting `<namespace>` and `<language>` with the user's answers from step 1.
   - `_prompts/` — empty folder (skills replace these)
5. Create `_templates/Template - Infinite Node.md` from `templates/node-template.md`.
6. Operating block: skip this step entirely when invoked from `/setup-ib` — it owns the operating block and has already written it. Otherwise, only if **neither** `CLAUDE.md` nor `AGENTS.md` exists at the vault root, create `CLAUDE.md` pointing agents to `_system/AGENTS.md` and the 5 skills — use the setup-ib seed (`../setup-ib/vault-claude-block.md`) as the body, filling in the namespace from step 1. If either file already exists, leave it untouched and tell the user to run `/setup-ib`, which merges the `## Infinite Brain vault` block into the existing file correctly.
7. Create two example nodes in the user's chosen namespace, adapting `templates/example-pillar.md` and `templates/example-decision.md` (rename IDs, set `namespace`, keep the full frontmatter + 50-300 word body shape). Write the human-readable content — `title`, `summary`, body prose, edge `note` fields — in the document language from step 1; keep `id` slugs, `type`, `visibility`, `namespace`, and `tags` in canonical English:
   - `pillars/pillar-[namespace]-foundation.md`
   - `decisions/decision-[namespace]-first.md`
   - Wire them with a `supports` edge.
8. Update `_system/INDEX.md` with both example nodes.
9. Confirm: "Vault initialized. X folders created, 2 example nodes wired. Open in Obsidian and run /convert-note to start ingesting content."

---

The files under `templates/` are adapted from [JotaSXBR/obsidian-infinite-brain](https://github.com/JotaSXBR/obsidian-infinite-brain) (MIT).
