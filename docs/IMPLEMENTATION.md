# Implementation Tracker

Master status tracker for the vision-driven GitHub release CLI. This file is the single source of truth for "where are we?" — every other doc is either reference material (`ARCHITECTURE.md`), a phase detail file (`phases/`), or a running log (`ITERATION-LOG.md`).

## Project at a glance

- **Goal**: A Python CLI that uses a vision-capable model + Playwright to autonomously navigate from a starting URL to a GitHub repo's releases page based on a free-form natural-language prompt, with **no hardcoded CSS/XPath selectors**.
- **CLI shape**:
  ```bash
  python navigate.py --url "https://github.com" \
    --prompt "search for openclaw and get the current release and related tags"
  ```
- **Final output** (stdout JSON):
  ```json
  {
    "repository": "owner/repo",
    "latest_release": "Release title",
    "version": "x.y.z",
    "tag": "vX.Y.Z",
    "author": "github_username"
  }
  ```

## Stack

- Python 3.10+
- [Playwright](https://playwright.dev/python/) (Chromium)
- Vision backends (via `create_vision_client()`):
  - **Ollama** (default) — cloud (`https://ollama.com` + `OLLAMA_API_KEY`) or local (`http://localhost:11434`)
  - **Gemini** (optional) — `google-genai`, requires `GOOGLE_API_KEY`
- Default Ollama model: **`qwen2.5vl:3b`** (override with `OLLAMA_MODEL` or `--model`)
- Pydantic v2 for action schema validation
- `python-dotenv` for env configuration

## Phase index

Each phase has its own file under `phases/`. Update both the table here **and** the status block inside the phase file when you change state.

| # | Phase | File | Status | Owner | Notes |
|---|---|---|---|---|---|
| 01 | Repo scaffold | [phases/01-scaffold.md](phases/01-scaffold.md) | Done | — | `agent/`, `requirements.txt`, `.gitignore` |
| 02 | Playwright browser wrapper | [phases/02-browser-wrapper.md](phases/02-browser-wrapper.md) | Done | — | `agent/browser.py` |
| 03 | Vision client | [phases/03-vision-client.md](phases/03-vision-client.md) | Done | — | `schema.py`, `ollama_client.py`, `gemini_client.py`, `vision.py` |
| 04 | Agent loop | [phases/04-agent-loop.md](phases/04-agent-loop.md) | Done | — | `agent/loop.py` |
| 05 | CLI wiring & output | [phases/05-cli-wiring.md](phases/05-cli-wiring.md) | Done | — | `navigate.py` |
| 06 | Documentation | [phases/06-docs.md](phases/06-docs.md) | Done | — | README + docs synced; demo artifacts optional |
| 07 | Smoke test & iteration | [phases/07-smoke-test.md](phases/07-smoke-test.md) | Cancelled | — | Ad-hoc runs only; formal smoke matrix dropped |

**Status legend**: `Not started` → `In progress` → `Blocked` → `Done`.

## Current focus

> Update this section at the start of every working session.

- **Active phase**: None — submission-ready.
- **Blockers**: None.

## Definition of done (whole project)

- [x] `python navigate.py --url https://github.com --prompt "..."` exits 0 and prints valid JSON (verified: `facebook/react` → `19.2.6`, 9 steps).
- [x] No CSS/XPath selectors anywhere in `agent/` (verified by `rg "querySelector|locator\(|xpath" agent/`).
- [x] README explains setup (venv, Playwright, Ollama/Gemini, `.env`), usage, design rationale, and known limitations.
- [x] `.env` is gitignored; no secrets committed.

## How to use these docs

- Working on a phase → open its file, flip status to `In progress`, tick off tasks as you go.
- Hit something unexpected → drop a dated entry in [ITERATION-LOG.md](ITERATION-LOG.md).
- Idea you don't want to lose but isn't in scope → [BACKLOG.md](BACKLOG.md).
- Need to understand the system → [ARCHITECTURE.md](ARCHITECTURE.md).
