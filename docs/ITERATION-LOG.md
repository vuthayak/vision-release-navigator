# Iteration Log

Reverse-chronological log of meaningful changes, learnings, and decisions. New entries go at the **top**. Entries are cheap — err on the side of writing one.

## Entry template

```
## YYYY-MM-DD — short title

**Phase**: NN
**Trigger**: what made you change something (failed smoke test, bug, review feedback, etc.)
**Change**: what you actually did, in 1–3 bullets.
**Result**: what happened after (pass/fail, metric delta, screenshots link).
**Follow-ups**: anything spawned by this (link to BACKLOG entries or new phase tasks).
```

---

## 2026-05-31 — OpenClaw E2E complete (phase 14)

**Phase**: 14
**Trigger**: User re-ran canonical command after End-workflow and prompt fixes; exit 0 with committed artifact.
**Change**:
- [`openclaw-release.json`](../openclaw-release.json) at repo root: `openclaw/openclaw`, tag `v2026.5.30-beta.1`, partial notes, non-empty `downloads`.
- Tracker/docs: v3 milestone **Done**; phase 14 unblocked; IMPLEMENTATION + README + ARCHITECTURE synced.
**Result**: Phase 14 acceptance met; v3 definition-of-done E2E checkboxes ticked.
**Follow-ups**: Optional code-quality refactors from review (policy consolidation, loop enforcement of End on detail pages).

---

## 2026-05-31 — Long changelog scroll loop (openclaw E2E)

**Phase**: 14 follow-up
**Trigger**: OpenClaw run hit max steps 30 — model scrolled up/down through huge release notes hunting for Assets/header; invalid `scroll.amount: -1` JSON at steps 14 and 21.
**Change**:
- Prompt: long-changelog rule — partial notes OK, max 3 scrolls in detail view, never ping-pong up/down, emit done when mid-changelog with no title visible.
- `_normalize_action_payload`: negative scroll amount → `direction: up`, positive amount.
- Loop: `_scroll_oscillation_instruction()` and `_scroll_budget_instruction()` nudge model to emit done.
- Schema: accept empty downloads when reasoning says Assets not visible after scrolling.

**Result**: 49 tests pass. Re-run OpenClaw E2E.

**Follow-ups**: Commit `openclaw-release.json` on successful run.

---

## 2026-05-31 — OpenClaw E2E fixes: Sponsors mis-click, Back key, click JSON

**Phase**: 14 follow-up
**Trigger**: User E2E on `openclaw/openclaw` — step 06 clicked Sponsors not Releases; invalid click JSON at step 6; crash on `press_key` `"Back"`.
**Change**:
- Prompt: sidebar discrimination (Releases vs Sponsors/Sponsor/etc.); recover via repo name link, not Back.
- `browser.press_key()`: map Back/Forward to `page.go_back()` / `go_forward()`.
- `action_parse.py`: `_repair_click_coords()` for `"x":40, 149` and `y":278"` malformations; extended click salvage regex.

**Result**: 19 parse/browser tests pass. Re-run canonical OpenClaw command when API quota available.

**Follow-ups**: Complete phase 14 E2E; commit `openclaw-release.json`.

---

## 2026-05-30 — v3 ship: JSON normalization, comments, OpenClaw E2E blocked

**Phase**: 12–15
**Trigger**: v3 milestone plan; final validation target `openclaw/openclaw`; API rate limits hit same day.
**Change**:
- Added `_quote_bare_keys()` to `action_parse.py` lenient parse path; 3 new unit tests for unquoted keys.
- Inline comments across `loop.py`, `action_parse.py`, `browser.py`, `schema.py`, `vision_parse.py`, vision backends, `navigate.py`.
- Partial OpenClaw E2E: 25 steps to **2026.5.28 Latest** release detail before Ollama 429; debug screenshots in `screenshots/step_*`.
- Updated README, IMPLEMENTATION, ARCHITECTURE, BACKLOG, phase files 12–15; added v3 at-a-glance, lenient parse pipeline docs, README documentation table.

**Result**: **Code pass** — 41 unit tests green. E2E **blocked** — no `openclaw-release.json` yet; user to re-run canonical command when quota resets.

**Follow-ups**: Run phase 14 canonical command with `--output openclaw-release.json`; commit artifact; tick v3 E2E checkbox in IMPLEMENTATION.md.

---

## 2026-05-30 — Post-v2 hardening: time budget, scroll, JSON salvage

**Phase**: 11 follow-up
**Trigger**: Canonical runs hit 180s timeout; aggressive scrolling selected release `19.1.7` instead of `19.2.6`; Ollama truncated action JSON at step 6 (`column 34`).
**Change**:
- Raised default `time_budget_s` **180 → 420** in `agent/loop.py`.
- Rewrote scroll heuristics in `SYSTEM_PROMPT`: click Latest first, scroll amount 1–2 within release detail only, scroll up if wrong semver visible.
- Added truncated JSON repair/salvage in `parse_action()`; Ollama `num_predict: 1024`; shorter navigation reasoning in prompt; debug logging of invalid raw JSON.
- Backlog entry for action JSON normalization (array coords, missing scroll direction, unquoted keys).

**Result**: **Pass** — `--headed --debug` on `facebook/react`, 9 steps, exit 0, correct **19.2.6** with full v2 fields. Mid-run `[vision:ollama] invalid JSON` warnings still appear but run completes.

**Follow-ups**: ~~Implement backlog **Action JSON normalization** when ready.~~ Shipped in v3 (phase 12).

---

## 2026-05-30 — Phase 11: v2 E2E validation & docs

**Phase**: 11
**Trigger**: v2 implementation complete (phases 08–10); need end-to-end proof and doc sync.
**Change**:
- Ran `python navigate.py ... --headed --debug` (canonical): attempt 1 failed at step 7 (invalid Ollama JSON after retry); attempt 2 hit 180s time budget after 7 steps (slow cloud inference).
- Ran headless validation with 420s budget: exit 0 in 9 steps; all v2 fields populated (`published_at`, `release_notes`, two `downloads`).
- Updated `README.md` (v2 schema, limitations, Tested with v2), `ARCHITECTURE.md` (v2 shipped), `IMPLEMENTATION.md` (phases 08–11 Done).
- Confirmed `rg "querySelector|locator\(|xpath" agent/` — no matches.

**Result**: Initial validation **partial pass** (extended-budget headless run populated all v2 fields but selected `19.1.7`). Superseded by post-v2 hardening entry above (`19.2.6`, 420s default).

**Sample output** (step 09):
```json
{
  "repository": "facebook/react",
  "latest_release": "19.1.7",
  "version": "19.1.7",
  "tag": "v19.1.7",
  "author": "eps1lon",
  "published_at": "May 6th, 2026",
  "release_notes": "React Server Components\n\n* Type hardening and performance improvements\n(#36425 by @eps1lon and @unstubbable)",
  "downloads": [
    { "name": "Source code (zip)", "url": "https://github.com/facebook/react/archive/refs/tags/v19.1.7.zip" },
    { "name": "Source code (tar.gz)", "url": "https://github.com/facebook/react/archive/refs/tags/v19.1.7.tar.gz" }
  ]
}
```

**Follow-ups**: Consider raising default `time_budget_s` for v2 or documenting longer runs; optional prompt tweak to prefer "Latest" semver over older stable entries.

---

## 2026-05-30 — Phase 09: rich extraction prompt

**Phase**: 09
**Trigger**: v2 requires vision model to gather publish date, release notes, and download assets before emitting `done`.
**Change**:
- Rewrote GitHub heuristics in `SYSTEM_PROMPT` with per-field mapping for `published_at`, `release_notes`, and `downloads`.
- Added scroll-within-release strategy, anti-hallucination clause for URLs, eight-field stop condition, and abbreviated example `done` JSON.
- Documented recommendation to raise `max_steps` from 25 to 30 in phase 10.

**Result**: Prompt mentions all eight output fields and ties v2 fields to visual regions; no selectors added.

**Follow-ups**: Phase 10 (`is_incomplete_extraction`, CLI stdout, optional `max_steps` bump).

---

## 2026-05-30 — Phase 10: loop & CLI v2 wiring

**Phase**: 10
**Trigger**: Phase 08 schema landed; loop and CLI still emitted v1 five-field JSON and blank-done guard.
**Change**:
- Extended `is_incomplete_extraction()` to require non-empty `published_at` and `release_notes`; empty `downloads` allowed.
- `_done_payload()` and stdout/`--output` now serialize all eight v2 fields including nested downloads.
- Default `max_steps` raised 25 → 30; exported `DownloadAsset` from `agent/vision.py`.

**Result**: Incomplete v2 extractions raise `AgentLoopError` → exit 1 (same as v1 blank done).

**Follow-ups**: Phase 09 (prompt heuristics for scroll/assets), phase 11 (E2E smoke, README).

---

## 2026-05-30 — Phase 08: extended `done` schema

**Phase**: 08
**Trigger**: v2 implementation — schema must precede prompt and CLI wiring.
**Change**:
- Added `DownloadAsset` and extended `DoneAction` with `published_at`, `release_notes`, `downloads` in `agent/schema.py`.
- Updated `SYSTEM_PROMPT` action list and task contract to reference eight payload fields (detailed heuristics deferred to phase 09).
- Verified `parse_action()` accepts v2 sample JSON; rejects v1-shaped and invalid `downloads` entries.

**Result**: `ACTION_JSON_SCHEMA` auto-includes nested downloads; acceptance checks pass locally.

**Follow-ups**: Phase 09 (full prompt heuristics), phase 10 (`_done_payload`, `is_incomplete_extraction`).

---

## 2026-05-30 — v2 planning: richer release metadata

**Phase**: 08–11 (planning)
**Trigger**: User scoped v2 to BACKLOG item "Richer release metadata" — release notes, download links, publish dates.
**Change**:
- Added v2 milestone to `IMPLEMENTATION.md` with phases 08–11 and definition of done.
- Created phase files: extended schema, prompt heuristics, loop/CLI wiring, validation & docs.
- Updated `ARCHITECTURE.md` (action schema, navigation flow, failure modes, milestones).
- Moved richer metadata from `BACKLOG.md` active work; kept `--repo` and flexible prompts as post–v2.

**Result**: Planning complete; implementation not started (phase 08 next).

**Follow-ups**: Implement phase 08 (`DownloadAsset`, extended `DoneAction`).

---

## 2026-05-30 — End-to-end verified: facebook/react

**Phase**: 07 (ad-hoc)
**Trigger**: Final submission check — confirm full navigation flow works on Ollama Cloud.
**Change**: None (validation run only).

**Command**:
```bash
python navigate.py \
  --url "https://github.com" \
  --prompt "search for facebook/react and get the latest release info" \
  --headed --debug
```

**Result**: Exit 0 in 9 steps. Output:
```json
{
  "repository": "facebook/react",
  "latest_release": "19.2.6 (May 6th, 2026)",
  "version": "19.2.6",
  "tag": "v19.2.6",
  "author": "eps1lon"
}
```
Stable release (not pre-release) — matches ground truth. Flow: search bar → type → Enter → wait → click repo → wait → click Releases (×2) → `done`.

**Follow-ups**: Added "Tested with" block to README; definition of done checked off in `IMPLEMENTATION.md`.

---

## 2026-05-30 — Drop formal smoke matrix

**Phase**: 07
**Trigger**: Scope review — 5-repo test matrix was unnecessary for the current project goals.
**Change**:
- Cancelled phase 07 smoke matrix and `smoke-results.md` deliverable.
- Kept ad-hoc iteration via real `--headed --debug` runs as sufficient validation.

**Result**: Phase 07 closed as iteration-only; no multi-repo matrix required before submit.

**Follow-ups**: Completed — see end-to-end verified entry above.

---

## 2026-05-30 — Ollama action JSON hardening

**Phase**: 03
**Trigger**: Ollama Cloud runs (`qwen3-vl:235b-cloud`) crashing mid-loop with Pydantic and JSON parse errors.
**Change**:
- **Missing `reasoning`**: model returned `{"action":"click","x":830,"y":40}` despite schema — added `_normalize_action_payload()` to default `reasoning` to `""`; strengthened `SYSTEM_PROMPT` with a required-field example.
- **Malformed JSON**: `json.loads` failed at step 7 (`JSONDecodeError` at column 27, likely unquoted keys) — added `_loads_action_json()` (fence strip, embedded-object extract, trailing-comma repair, `ast.literal_eval` fallback for single-quoted dicts).
- Renamed `validation_retry_message` → `action_retry_message`; both `ollama_client.py` and `gemini_client.py` now retry on `JSONDecodeError` and `ValidationError`.

**Result**: Parser crashes eliminated. Observed run progressed steps 1–7 (search → type → Enter → wait → refresh on GitHub load error). Remaining flakiness is model navigation behavior, not response parsing.

**Follow-ups**: None blocking submission.

---

## 2026-05-30 — Documentation pass (code ↔ docs aligned)

**Phase**: 06
**Trigger**: Docs still described pre-migration Gemini-only stack, wrong defaults (`llama3.2-vision`), and stale phase statuses.
**Change**:
- Rewrote `README.md`: Ollama Cloud + local setup, dual provider, CLI flags, navigation flow, project layout, troubleshooting.
- Updated `ARCHITECTURE.md`, `IMPLEMENTATION.md`, and all `phases/*.md` to match current file layout (`schema.py`, `ollama_client.py`, `gemini_client.py`, `vision.py`).
- Marked phases 01–05 and 03 **Done**; phase 06 substantially complete.

**Result**: Docs match the codebase as of this session. Demo GIF and "Tested with" block remain optional polish.

**Follow-ups**: Add "Tested with" line to README after a clean run, if desired.

---

## 2026-05-30 — Ollama Cloud as default backend

**Phase**: 03
**Trigger**: User wants Ollama Cloud instead of local GPU inference.
**Change**:
- Default `OLLAMA_HOST` → `https://ollama.com`; require `OLLAMA_API_KEY` for cloud hosts.
- `OllamaVisionClient` sends `Authorization: Bearer` header; local localhost still works without a key.

**Result**: Verified with cloud API key in `.env`; runs reach vision inference (`[vision:ollama:cloud]` in debug output).

**Follow-ups**: None — superseded by JSON hardening entry above.

---

## 2026-05-30 — Dual-provider vision refactor (Ollama + Gemini)

**Phase**: 03
**Trigger**: Gemini free-tier rate limits (5 req/min); need a local/cloud Ollama path alongside Gemini fallback.
**Change**:
- Split vision layer: `agent/schema.py`, `agent/ollama_client.py`, `agent/gemini_client.py`, factory in `agent/vision.py`.
- CLI: `--provider ollama|gemini` (default ollama), `--ollama-host`, model defaults `qwen2.5vl:3b` / `gemini-2.5-flash`.
- Updated `requirements.txt`, `.env.example`, `ARCHITECTURE.md`.

**Result**: Both backends wired end-to-end. Ollama Cloud used for primary iteration.

**Follow-ups**: Completed — see JSON hardening and docs pass entries.

---

## 2026-05-30 — Provider switch planning (docs only)

**Phase**: 03, 06
**Trigger**: Decision to move primary backend from Gemini to Ollama while keeping the vision + Playwright architecture.
**Change**:
- Drafted doc updates describing Ollama env vars and setup flow.
- Set interim phase statuses before code migration landed.

**Result**: Planning entry only. Code migration completed same day — see dual-provider refactor entry.

**Follow-ups**: N/A (historical).

---

## 2026-05-28 — Releases-anchored stable extraction

**Phase**: 04 (prompt iteration)
**Trigger**: `facebook/react` run returned pre-release `v18.3.0-next-...` instead of stable `19.2.6`; model picked topmost card on releases page.
**Change**:
- Rewrote `SYSTEM_PROMPT` (then in `agent/schema.py`, now `agent/prompts.py`): anchor on visible "Releases" label, scan region below/beside it, skip pre-release badges and `-next`/`-rc` tags, prefer "Latest" or newest stable semver, scroll if needed.
- Clarified field mapping (`latest_release` = title, not tag).
- Updated `ARCHITECTURE.md` system prompt sketch to match.

**Result**: Partial validation on Gemini before rate-limit block — step 6 changed from immediate `done` on pre-release to `scroll` toward stable release. Full re-run deferred until Ollama migration.

**Follow-ups**: Re-validated behavior during Ollama Cloud runs (2026-05-30); formal multi-repo matrix cancelled.

---

## 2026-05-28 — Project kickoff

**Phase**: 00 (planning)
**Trigger**: Take-home assignment scoped with the user.
**Change**:
- Decided on vision model + Playwright Chromium architecture (Gemini 2.5 Flash initially; Ollama added as primary backend).
- CLI shape locked: `python navigate.py --url <url> --prompt <free-text>`.
- Output schema locked to `{repository, latest_release, version, tag, author}`.
- Created docs tracker (`IMPLEMENTATION.md`), architecture reference (`ARCHITECTURE.md`), seven phase files, this log, and backlog.

**Result**: Plan committed; phases 01–07 executed through phase 05 + iteration.

**Follow-ups**: Completed — see 2026-05-30 entries.
