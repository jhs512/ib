---
name: setup-ib
description: Sets up the Infinite Brain vault operating context in a repo or folder — writes an `## Infinite Brain vault` block (operating rules + ib skills table + node/edge quick reference) into CLAUDE.md/AGENTS.md and ensures the `_system/` scaffolding exists, so the ib skills know this directory is a knowledge-graph vault. Run once before first use of `init-vault`, `convert-note`, `query-vault`, `organize-vault`, or `vault-health` — or if those skills appear to be missing vault context (taxonomy, namespace, `_system/` entry points).
disable-model-invocation: true
---

# Setup Infinite Brain (ib) skills

Scaffold the per-vault configuration that the **ib** skills assume:

- **Operating block** — an `## Infinite Brain vault` section in `CLAUDE.md` (or `AGENTS.md`) so every agent knows this directory is a typed-node / typed-edge knowledge graph, and which `/`-commands operate on it.
- **`_system/` entry points** — `AGENTS.md` (taxonomy, visibility model, frontmatter schema, prohibited actions) and `INDEX.md` (the master node index every new node must update).
- **Defaults** — the starting namespace and the default node visibility.

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

### 3. Confirm and edit

Show the user a draft of:

- The `## Infinite Brain vault` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited (see step 4), with `<namespace>` and `<visibility>` filled in.
- The list of `_system/` files that will be created (if any), or "already present — leaving as-is".

Let them edit before writing.

### 4. Write

**Pick the file to edit:**

- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask the user which one to create — don't pick for them.

Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa) — always edit the one that's already there. If an `## Infinite Brain vault` block already exists in the chosen file, update its contents in place rather than appending a duplicate. Don't overwrite the user's edits to surrounding sections.

Write the block using the seed in this skill folder as a starting point — [vault-claude-block.md](./vault-claude-block.md) — substituting the namespace and visibility from Section B/C. When the vault lives in a subfolder, note the path in the block's first line ("The `vault/` directory is an AI-first knowledge-graph vault…").

Then ensure the `_system/` entry points exist:

- If the user opted into `/init-vault`, invoke it in the chosen location, passing along the namespace from Section B so it doesn't re-ask, and skip its operating-block step — the CLAUDE.md/AGENTS.md block is this skill's job and was just written above.
- Otherwise seed the minimum so the other ib skills have something to read: `_system/AGENTS.md` and `_system/INDEX.md` (empty per-type tables). For `AGENTS.md`, copy the seed in this skill folder — [vault-agents-template.md](./vault-agents-template.md) — substituting `<namespace>` from Section B; it carries the full operating rules (taxonomy, visibility model, frontmatter schema, log-writing rules, prohibited actions, first-session protocol). Leave any existing `_system/` file untouched.

### 5. Done

Tell the user setup is complete and which ib skills now have the context they need (`init-vault`, `convert-note`, `query-vault`, `organize-vault`, `vault-health`). Mention they can edit the `## Infinite Brain vault` block or `_system/*.md` directly later — re-running this skill is only needed to change the namespace/visibility defaults or relocate the vault.
