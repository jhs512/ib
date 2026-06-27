---
name: setup-gcp
description: Provisions the reusable Google Cloud credentials the Infinite Brain Google Sheets mirror needs — a GCP project (default `infinite-brain`), the Sheets + Drive APIs enabled, a service account, and a downloaded JSON key — and saves them to `~/.config/ib/sheets-sync.env` for reuse across every vault. Idempotent by design: it checks for an existing project / service account / key and REUSES them instead of creating duplicates (this skill exists because the old setup created a second GCP project on every run). Run this once per Google account; afterwards `setup-sheets-sync` reuses the saved credentials. Prefers the `gcloud` CLI for deterministic idempotency and falls back to driving the browser if `gcloud` isn't installed.
disable-model-invocation: true
---

# Setup Google Cloud credentials for the ib Sheets mirror

This skill provisions, **once per Google account**, the credentials shared by every vault's Google Sheets mirror:

- a **GCP project** (default name/slug `infinite-brain`),
- the **Google Sheets API** and **Google Drive API** enabled on it,
- a **service account** (default `ib-sheets-sync`),
- a **JSON key** for that service account, saved outside any repo.

It then records everything in `~/.config/ib/sheets-sync.env` so `setup-sheets-sync` (and future vaults) reuse it.

## The one rule: check, then create — never duplicate

Each resource below is **check-then-create**. If it already exists, reuse it. The whole reason this skill is separate from `setup-sheets-sync` is that the old flow ran "create a GCP project" on every vault and left users with two or three duplicate projects. Do not create a second project, service account, or key when a usable one already exists. Only create a new key if none is on disk, or the user explicitly asks to rotate.

## 0. Short-circuit if already provisioned

Read `~/.config/ib/sheets-sync.env` if it exists. If it already defines `GCP_PROJECT_ID`, `SA_EMAIL`, and a `SA_KEY_PATH` that points to a real file, the account is already set up — report the existing values and stop, unless the user explicitly wants to re-provision or rotate the key. There is nothing per-vault here; this skill never needs to run twice for the same account.

## 1. Pick the path: gcloud (preferred) or browser

Check whether `gcloud` is installed and authenticated (`gcloud --version`, `gcloud auth list`).

- **Installed & authed** → use the gcloud path (§2). It makes existence checks deterministic — the cleanest way to stay idempotent.
- **Not installed** → offer the user a choice:
  - **Install gcloud** (recommended) — point them at <https://cloud.google.com/sdk/docs/install>, then `gcloud auth login`. Resume at §2. (Suggest they run the login via `! gcloud auth login` so its output lands in this session.)
  - **Browser fallback** — drive the Cloud Console by hand (§3). Confirm a browser-driving tool is actually available first (the `claude-in-chrome` skill or a Chrome/DevTools MCP). If none is available, stop and ask the user to enable one — doing the console steps blind is error-prone.

Ask the user for the project slug; default `infinite-brain`. Ask for the service-account name; default `ib-sheets-sync`.

## 2. gcloud path (idempotent)

Let `SLUG` be the chosen project slug (default `infinite-brain`) and `SA` the service-account name (default `ib-sheets-sync`).

1. **Project — reuse or create.**
   ```bash
   gcloud projects list --filter="name:$SLUG OR projectId:$SLUG" --format="value(projectId)"
   ```
   - If a row comes back, **reuse** that `projectId` (show it to the user and confirm it's the right one if several match).
   - If empty, create it. GCP project IDs are globally unique, so the bare slug may be taken by someone else; append a short numeric suffix only if needed:
     ```bash
     gcloud projects create "$SLUG" --name="$SLUG"   # retry as "$SLUG-NNNNNN" on collision
     ```
   Record the resulting id as `GCP_PROJECT_ID`. Set it active: `gcloud config set project "$GCP_PROJECT_ID"`.

2. **Enable APIs** (enabling an already-enabled API is a no-op):
   ```bash
   gcloud services enable sheets.googleapis.com drive.googleapis.com --project="$GCP_PROJECT_ID"
   ```

3. **Service account — reuse or create.**
   ```bash
   gcloud iam service-accounts list --project="$GCP_PROJECT_ID" --format="value(email)"
   ```
   - If an account matching `$SA@$GCP_PROJECT_ID.iam.gserviceaccount.com` exists, **reuse** it.
   - Otherwise create it:
     ```bash
     gcloud iam service-accounts create "$SA" --display-name="ib sheets sync" --project="$GCP_PROJECT_ID"
     ```
   Record the email as `SA_EMAIL`.

4. **JSON key — reuse on disk, only create if missing.** The canonical location is `~/.config/ib/sheets-sync-sa.json`.
   - If that file already exists, **reuse it** — do not generate another key (each new key is a fresh live credential to manage). Record `SA_KEY_PATH`.
   - If it's missing (or the user explicitly wants to rotate), create one:
     ```bash
     mkdir -p ~/.config/ib
     gcloud iam service-accounts keys create ~/.config/ib/sheets-sync-sa.json --iam-account="$SA_EMAIL"
     ```
   Unlike the browser path, the gcloud `keys create` is allowed to write the file directly (the user invoked this skill and chose this path). Tell the user a live credential was written and where.

## 3. Browser fallback (idempotent by inspection)

Drive the Cloud Console, but **check before every create**:

1. **Project — reuse or create.** Open the project picker (`console.cloud.google.com` → project dropdown) or `console.cloud.google.com/cloud-resource-manager`. **Search the list for the slug first.** If a project named `infinite-brain` exists, select it — do **not** open `projectcreate`. Only if it's absent, go to `console.cloud.google.com/projectcreate` and create it. Capture the project id.
2. **Enable APIs.** For the active project, enable **Google Sheets API** and **Google Drive API** (`console.cloud.google.com/apis/library`). If the library already shows "API Enabled", skip.
3. **Service account — reuse or create.** Open `console.cloud.google.com/iam-admin/serviceaccounts`. If `ib-sheets-sync@…` is listed, reuse it; otherwise create it. Record `client_email`.
4. **JSON key — ★ human downloads.** Under the service account → Keys → Add key → Create new key → JSON. **The human clicks the final "Create"/accepts the download** — never do a credential download silently. Have them move/save the file to `~/.config/ib/sheets-sync-sa.json` (create the folder if needed). Confirm the path with them.

## 4. Persist for reuse

Write `~/.config/ib/sheets-sync.env` (create `~/.config/ib/` first) so later skills and vaults don't repeat any of this:

```sh
GCP_PROJECT_ID=<project id>
SA_EMAIL=<service-account email>
SA_KEY_PATH=<absolute path to the JSON key, e.g. ~/.config/ib/sheets-sync-sa.json>
```

If the file already exists, update the values in place rather than duplicating keys.

## 5. Done

Report the project id, service-account email, and key path, and remind the user the key file is a **live credential** — keep it out of any repo and rotate it later in GCP if needed. Tell them this is reusable: every vault's `/setup-sheets-sync` will pick these up automatically, so they won't run `/setup-gcp` again unless they want a different project or a rotated key. Next step for a given vault: **`/setup-sheets-sync`**.
