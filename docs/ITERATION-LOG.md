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
**Trigger**: Submission scope review — 5-repo test matrix is unnecessary for the take-home deliverable.
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
- Rewrote `SYSTEM_PROMPT` (now in `agent/schema.py`): anchor on visible "Releases" label, scan region below/beside it, skip pre-release badges and `-next`/`-rc` tags, prefer "Latest" or newest stable semver, scroll if needed.
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
