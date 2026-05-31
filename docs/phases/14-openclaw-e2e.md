# Phase 14 — OpenClaw E2E + sample output artifact (v3)

## Goal

Final validation on `openclaw/openclaw` and commit real extracted JSON as `openclaw-release.json` at repo root.

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-31

## Canonical command

```bash
python navigate.py \
  --url "https://github.com" \
  --prompt "search for openclaw and get the current release and related tags" \
  --output openclaw-release.json \
  --headed --debug
```

## Partial run (2026-05-30)

Headless attempt with Ollama Cloud `qwen3-vl:235b-cloud`:

- **Steps completed**: 25 of 30 before Ollama session usage limit (HTTP 429).
- **Navigation path**: github.com → search "openclaw" → repo → releases → **openclaw 2026.5.28 Latest** detail view.
- **Mid-run JSON**: one invalid JSON at step 5 (`x:327, y":278"` — mixed quoting); retry succeeded at step 6.
- **Stall**: agent scrolled 15× looking for Assets section; run terminated on rate limit at step 26 request.
- **Debug artifacts**: `screenshots/step_01.png` … `step_25.png` (+ matching `.json` action files).

## Successful run (2026-05-31)

Canonical command exited 0. Artifact at repo root: [`openclaw-release.json`](../../openclaw-release.json).

- **Target release**: topmost on list — **v2026.5.30-beta.1** (newest published; pre-release at top per v3 heuristics).
- **Fields**: all eight v2 fields populated; partial `release_notes`; `downloads` includes Source code zip/tar.gz from tag.
- **End workflow**: jump-to-bottom (`press_key End`) used to reach Assets without scrolling the full changelog.

## Tasks

- [x] Run canonical command to exit 0 with all v2 fields populated.
- [x] Spot-check against GitHub UI: topmost release (v2026.5.30-beta.1 above stable **Latest** row).
- [x] Commit `openclaw-release.json` at repo root (same JSON as stdout).
- [x] README documents sample artifact path and generation command.
- [x] `openclaw-release.json` is **not** gitignored (tracked at repo root).

## Acceptance criteria

- Exit 0 on `openclaw/openclaw` with eight v2 fields populated.
- `openclaw-release.json` at repo root matches stdout output.
- README "Tested with" v3 section cites run date, model, and step count.

## Dependencies

- Phases 12–13 complete.
