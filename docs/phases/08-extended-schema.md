# Phase 08 — Extended output schema

## Goal

Extend the `done` action and Pydantic models in `agent/schema.py` so the agent can return release notes, download links, and publish dates alongside the existing five v1 fields.

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

## Deliverables

- `DownloadAsset` model: `{ name: str, url: str }`.
- Extended `DoneAction` with three new fields:
  - `published_at: str`
  - `release_notes: str`
  - `downloads: list[DownloadAsset]` (default `[]`)
- Updated `ACTION_JSON_SCHEMA` (auto-regenerated from Pydantic).
- Updated `SYSTEM_PROMPT` action list line (full prompt rewrite in phase 09).

## Target schema

```python
class DownloadAsset(BaseModel):
    name: str
    url: str


class DoneAction(BaseModel):
    action: Literal["done"]
    repository: str
    latest_release: str
    version: str
    tag: str
    author: str
    published_at: str
    release_notes: str
    downloads: list[DownloadAsset] = Field(default_factory=list)
    reasoning: str
```

## JSON example (contract)

```json
{
  "repository": "facebook/react",
  "latest_release": "19.2.6 (May 6th, 2026)",
  "version": "19.2.6",
  "tag": "v19.2.6",
  "author": "eps1lon",
  "published_at": "May 6th, 2026",
  "release_notes": "## What's Changed\n\n* Fix suspense boundary ...",
  "downloads": [
    { "name": "Source code (zip)", "url": "https://github.com/facebook/react/archive/refs/tags/v19.2.6.zip" },
    { "name": "Source code (tar.gz)", "url": "https://github.com/facebook/react/archive/refs/tags/v19.2.6.tar.gz" }
  ]
}
```

## Tasks

- [x] Add `DownloadAsset` model.
- [x] Extend `DoneAction` with `published_at`, `release_notes`, `downloads`.
- [x] Confirm `ACTION_JSON_SCHEMA` includes nested `downloads` items (both Ollama `format=` and Gemini structured output must receive the updated schema).
- [x] Update the one-line `done` description in `SYSTEM_PROMPT` to list all eight payload fields (detailed extraction rules deferred to phase 09).
- [x] Grep for `DoneAction` / five-field assumptions in `agent/` and `navigate.py`; note call sites for phase 10.

## Acceptance criteria

- `parse_action()` in `action_parse.py` validates a sample v2 `done` JSON with nested `downloads`.
- Invalid `downloads` entries (missing `name` or `url`) fail Pydantic validation and trigger provider retry.
- v1-shaped `done` JSON (missing new fields) fails validation — v2 is a breaking schema change; no backward-compat shim required.

## Dependencies

- v1 phases 01–05 complete.

## Risks

- **Large `release_notes` in JSON**: long bodies inflate token usage on the final `done` turn. Mitigate by instructing the model to copy visible text faithfully but not invent content; truncation in the screenshot is acceptable in the extracted string.
- **URL hallucination**: vision models may guess URLs not visible on screen. Phase 09 prompt must require URLs only when readable (hover tooltip, visible href text, or standard GitHub asset naming patterns on the releases page).

## Notes

- Keep `downloads` as an array of objects, not a flat dict — asset names vary (`Source code (zip)`, `.dmg`, `.msi`, etc.).
- Do not add a GitHub API client or DOM scraping helper; schema-only change in this phase.

## Phase 10 follow-up (call sites)

- `navigate.py` — `_done_payload()` still emits five v1 keys only; extend in phase 10.
- `agent/loop.py` — `is_incomplete_extraction()` checks five fields only; extend blank-done guard in phase 10.
