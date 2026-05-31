# Implementation Tracker

Master status tracker for the vision-driven GitHub release CLI. This file is the single source of truth for "where are we?" — every other doc is either reference material (`ARCHITECTURE.md`), a phase detail file (`phases/`), or a running log (`ITERATION-LOG.md`).

## Milestones

| Milestone | Scope | Status |
|---|---|---|
| **v1** | Five-field release snapshot via vision navigation | **Done** (2026-05-30) |
| **v2** | Richer metadata: release notes, download links, publish date | **Done** (2026-05-30) |
| **v3** | JSON normalization, code comments, OpenClaw E2E artifact | **Done** (2026-05-31) |

---

## v1 summary (complete)

- **Goal**: Navigate from a starting URL to a GitHub repo's releases page using vision + Playwright — **no CSS/XPath selectors** — and return the latest **stable** release as JSON.
- **Output** (five fields): `repository`, `latest_release`, `version`, `tag`, `author`.
- **Verified**: `facebook/react` → `19.2.6`, 9 steps, all v2 fields, Ollama Cloud `qwen3-vl:235b-cloud` (see iteration log).

---

## v2 at a glance

- **Goal**: Extend the `done` action and CLI output with richer fields visible on the GitHub releases page, still extracted entirely from screenshots (no selectors, no GitHub API).
- **New fields**:

  ```json
  {
    "repository": "owner/repo",
    "latest_release": "Release title",
    "version": "x.y.z",
    "tag": "vX.Y.Z",
    "author": "github_username",
    "published_at": "May 6th, 2026",
    "release_notes": "Full or partial release body text as read from the page.",
    "downloads": [
      { "name": "Source code (zip)", "url": "https://github.com/owner/repo/archive/refs/tags/vX.Y.Z.zip" },
      { "name": "example-binary.tar.gz", "url": "https://github.com/owner/repo/releases/download/vX.Y.Z/example-binary.tar.gz" }
    ]
  }
  ```

- **Field rules**:
  - `published_at` — date string exactly as shown on the release card (relative dates like "2 weeks ago" are acceptable if that's what's visible).
  - `release_notes` — markdown/plain text from the release body under the title; scroll within the release if truncated. Empty string only if the body is genuinely absent.
  - `downloads` — array of `{name, url}` for each asset in the **Assets** section of the stable release; scroll if assets are below the fold. Empty array if no assets are listed.

- **Non-goals for v2** (moved to [BACKLOG.md](BACKLOG.md) post-v3): `--repo` flag, open-ended output schema, GitHub API fallback, multi-release comparison.

---

## v3 at a glance

- **Goal**: Harden Ollama action JSON parsing, improve code readability with inline comments, and produce a committed sample output artifact from `openclaw/openclaw`.
- **Shipped (code)**:
  - `_quote_bare_keys()` in `agent/action_parse.py` — quotes bare JSON keys (`x:620`) before `json.loads` in the lenient path.
  - Line-level inline comments in core `agent/` modules and `navigate.py`.
  - Phase docs 12–15; tracker and README synced.
- **E2E**: [`openclaw-release.json`](../openclaw-release.json) at repo root from successful run on `openclaw/openclaw` (2026-05-31) — topmost release **v2026.5.30-beta.1**, partial notes, Source code downloads (see [phases/14-openclaw-e2e.md](phases/14-openclaw-e2e.md)).

**Canonical E2E command**:

```bash
python navigate.py \
  --url "https://github.com" \
  --prompt "search for openclaw and get the current release and related tags" \
  --output openclaw-release.json \
  --headed --debug
```

## Stack

Unchanged from v1:

- Python 3.10+
- Playwright (Chromium)
- Vision backends: Ollama (default), Gemini (optional)
- Pydantic v2, `python-dotenv`

## Phase index

### v1 (complete)

| # | Phase | File | Status | Notes |
|---|---|---|---|---|
| 01 | Repo scaffold | [phases/01-scaffold.md](phases/01-scaffold.md) | Done | |
| 02 | Playwright browser wrapper | [phases/02-browser-wrapper.md](phases/02-browser-wrapper.md) | Done | |
| 03 | Vision client | [phases/03-vision-client.md](phases/03-vision-client.md) | Done | |
| 04 | Agent loop | [phases/04-agent-loop.md](phases/04-agent-loop.md) | Done | |
| 05 | CLI wiring & output | [phases/05-cli-wiring.md](phases/05-cli-wiring.md) | Done | |
| 06 | Documentation | [phases/06-docs.md](phases/06-docs.md) | Done | |
| 07 | Smoke test & iteration | [phases/07-smoke-test.md](phases/07-smoke-test.md) | Cancelled | Ad-hoc runs only |

### v2 (complete)

| # | Phase | File | Status | Notes |
|---|---|---|---|---|
| 08 | Extended output schema | [phases/08-extended-schema.md](phases/08-extended-schema.md) | Done | `DoneAction`, JSON schema, types |
| 09 | Prompt & extraction heuristics | [phases/09-rich-extraction-prompt.md](phases/09-rich-extraction-prompt.md) | Done | `SYSTEM_PROMPT`, scroll guidance, anti-hallucination |
| 10 | Loop & CLI output | [phases/10-loop-cli-v2.md](phases/10-loop-cli-v2.md) | Done | blank-done check, stdout JSON |
| 11 | Validation & docs | [phases/11-v2-validation-docs.md](phases/11-v2-validation-docs.md) | Done | E2E v2 on `facebook/react`; post-ship hardening in iteration log |

### v3 (complete)

| # | Phase | File | Status | Notes |
|---|---|---|---|---|
| 12 | Action JSON normalization | [phases/12-action-json-normalization.md](phases/12-action-json-normalization.md) | Done | `_quote_bare_keys`, unquoted-key tests |
| 13 | Code comments | [phases/13-code-comments.md](phases/13-code-comments.md) | Done | Inline comments in core modules |
| 14 | OpenClaw E2E + sample JSON | [phases/14-openclaw-e2e.md](phases/14-openclaw-e2e.md) | Done | `openclaw-release.json`; v2026.5.30-beta.1 |
| 15 | Validation & docs | [phases/15-v3-validation-docs.md](phases/15-v3-validation-docs.md) | Done | Tracker sync |

**Status legend**: `Not started` → `In progress` → `Blocked` → `Done`.

## Current focus

> Update this section at the start of every working session.

- **Active milestone**: v3 — **complete** (2026-05-31).
- **Active phase**: none (all v3 phases done).
- **Blockers**: none.

## Post-ship defaults (2026-05-30)

- **`time_budget_s`**: 420s in `agent/loop.py` (was 180s).
- **`max_steps`**: 30 (CLI + loop).
- **Ollama**: `num_predict: 1024`; lenient parse in `action_parse.py` (`parse_action_lenient()`): truncated JSON salvage, `_quote_bare_keys()` for unquoted keys, array-coord normalization.
- **Prompt**: gentle scroll-within-release heuristics to avoid selecting older stable releases.
- **Comments**: inline annotations in loop, browser, schema, action_parse, vision backends, and CLI (phase 13).

## Definition of done

### v1 (complete)

- [x] `python navigate.py --url https://github.com --prompt "..."` exits 0 and prints valid five-field JSON.
- [x] No CSS/XPath selectors anywhere in `agent/`.
- [x] README explains setup, usage, design rationale, and known limitations.
- [x] `.env` is gitignored; no secrets committed.

### v2 (complete)

- [x] `DoneAction` and `ACTION_JSON_SCHEMA` include `published_at`, `release_notes`, and `downloads`.
- [x] `SYSTEM_PROMPT` instructs the model to scroll for truncated notes and Assets before emitting `done`.
- [x] Agent loop treats blank v2 fields as incomplete (same pattern as v1 five-field check).
- [x] `navigate.py` prints the extended JSON shape on stdout (and `--output`).
- [x] End-to-end verification on `facebook/react`: all v2 fields populated; latest stable **19.2.6** in 9 steps with `--headed --debug` (2026-05-30).
- [x] README and `ARCHITECTURE.md` document the v2 output contract and updated limitations.
- [x] No CSS/XPath selectors introduced in `agent/` (`rg` clean).

### v3 (target)

- [x] `_quote_bare_keys()` handles unquoted JSON keys in `parse_action_lenient()` with unit tests.
- [x] Core modules have line-level inline comments on non-obvious logic.
- [x] E2E on `openclaw/openclaw` exits 0 with all v2 fields populated (2026-05-31).
- [x] `openclaw-release.json` committed at repo root from real run (`--output openclaw-release.json`).
- [x] README, `ARCHITECTURE.md`, `BACKLOG.md`, and phase index updated for v3.

## How to use these docs

- Working on a phase → open its file, flip status to `In progress`, tick off tasks as you go.
- Hit something unexpected → drop a dated entry in [ITERATION-LOG.md](ITERATION-LOG.md).
- Idea you don't want to lose but isn't in current scope → [BACKLOG.md](BACKLOG.md).
- Need to understand the system → [ARCHITECTURE.md](ARCHITECTURE.md).
