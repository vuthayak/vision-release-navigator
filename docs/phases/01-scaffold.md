# Phase 01 — Repo scaffold

## Goal

Stand up the project skeleton so subsequent phases have a place to write code, dependencies are pinned, and secrets stay out of git.

## Status

- **State**: Done
- **Started**: 2026-05-28
- **Completed**: 2026-05-30

## Deliverables

- `navigate.py` (entrypoint — full wiring in phase 05).
- `agent/__init__.py` (empty package marker).
- `requirements.txt` with: `playwright`, `ollama`, `google-genai`, `pydantic>=2`, `python-dotenv`.
- `.env.example` for `VISION_PROVIDER`, `OLLAMA_HOST`, `OLLAMA_API_KEY`, `OLLAMA_MODEL`, `GOOGLE_API_KEY`.
- `.gitignore` covering `.env`, `__pycache__/`, `screenshots/`, `*.png`, `.venv/`.
- Remove placeholder `hello.py`.

## Tasks

- [x] Delete `hello.py`.
- [x] Create `agent/` package with empty `__init__.py`.
- [x] Create `navigate.py` (CLI implemented in phase 05).
- [x] Write `requirements.txt`. Lower bounds (`>=`); phase 07 locks after smoke-testing.
- [x] Write `.env.example`.
- [x] Write `.gitignore`.
- [ ] Verify `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && playwright install chromium` succeeds locally.

## Acceptance criteria

- Running `python navigate.py` with required args drives the agent (phase 05).
- `git status` shows no `.env` and no `__pycache__` candidates.
- `pip install -r requirements.txt` resolves cleanly on a fresh venv.

## Dependencies

- None (this is the first phase).

## Risks

- Vision SDK choice affects `requirements.txt` — confirm `ollama` client version in phase 03 after migration.
- Playwright requires a one-time `playwright install chromium` step — flag it loudly in the README phase.

## Notes

- Use a `agent/` package (not flat modules) so phase 03+ can `from agent.browser import Browser` cleanly.
- Keep `navigate.py` at repo root because the user's example CLI calls it that way.
