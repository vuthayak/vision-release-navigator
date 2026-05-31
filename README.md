# aesopic-f26-take-home

Vision-driven CLI that navigates GitHub in a real browser (Playwright) using screenshot feedback from a vision model — no CSS/XPath selectors. Given a starting URL and a natural-language goal, it returns the latest **stable** release metadata as JSON.

Submission for the Fall 2026 Vision Agents co-op take-home (Aesopic Inc.).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

### Ollama (default provider)

**Ollama Cloud** (default in `.env.example`):

1. Create an API key at [ollama.com/settings/keys](https://ollama.com/settings/keys).
2. Set in `.env`:
   ```
   VISION_PROVIDER=ollama
   OLLAMA_HOST=https://ollama.com
   OLLAMA_API_KEY=your_key_here
   OLLAMA_MODEL=qwen3-vl:235b-cloud
   ```

**Local Ollama** (alternative):

```bash
ollama serve   # if not already running
ollama pull qwen2.5vl:3b   # or another local vision model
```

Set `OLLAMA_HOST=http://localhost:11434` and leave `OLLAMA_API_KEY` empty.

### Gemini (optional fallback)

Set `VISION_PROVIDER=gemini` and `GOOGLE_API_KEY` in `.env`, then run with `--provider gemini`.

## Usage

```bash
python navigate.py --url "https://github.com" \
  --prompt "search for openclaw and get the current release and related tags" \
  --headed --debug
```

More examples:

```bash
python navigate.py --url "https://github.com" \
  --prompt "search for facebook/react and get the latest release info"

python navigate.py --url "https://github.com" \
  --prompt "find microsoft vscode and tell me the most recent release"
```

| Flag | Default | Purpose |
|---|---|---|
| `--provider` | `ollama` | `ollama` or `gemini` |
| `--model` | `qwen3-vl:235b-cloud` (ollama) | Vision model id |
| `--ollama-host` | `https://ollama.com` | Ollama API base URL |
| `--max-steps` | 30 | Agent loop iteration cap |
| `--time-budget` | 420 | Wall-clock time limit in seconds |
| `--headed` / `--headless` | headed | Browser visibility |
| `--output PATH` | — | Also write final JSON to file |
| `--debug` | off | Step lines + vision timing on **stderr**; saves `screenshots/step_*` |

## Output

Eight fields on success (v2). The `downloads` array holds asset rows from the stable release’s **Assets** section; it may be empty when no assets are listed.

```json
{
  "repository": "owner/repo",
  "latest_release": "Release title",
  "version": "1.0.0",
  "tag": "v1.0.0",
  "author": "github_username",
  "published_at": "May 6th, 2026",
  "release_notes": "Full or partial release body text as read from the page.",
  "downloads": [
    { "name": "Source code (zip)", "url": "https://github.com/owner/repo/archive/refs/tags/v1.0.0.zip" },
    { "name": "example-binary.tar.gz", "url": "https://github.com/owner/repo/releases/download/v1.0.0/example-binary.tar.gz" }
  ]
}
```

| Field | Meaning |
|---|---|
| `repository` | `owner/repo` from page context |
| `latest_release` | Release **title** (not the tag) |
| `version` | Semver without leading `v` |
| `tag` | Tag as shown (e.g. `v1.0.0`) |
| `author` | Username on the stable release card |
| `published_at` | Date string as displayed (relative dates OK) |
| `release_notes` | Body text under the title; may be partial if truncated |
| `downloads` | `{name, url}` per asset row |

Printed to stdout (and optionally `--output`). With `--debug`, each step logs to **stderr** as `[step NN] action: reasoning…` plus Ollama timing; invalid JSON may log `[vision:ollama] invalid JSON` before auto-retry.

## How it navigates

The agent does not follow a hardcoded script. Each turn it screenshots the viewport, asks the vision model for **one** action, executes it, and repeats until it emits `done`.

For GitHub release tasks, the intended flow is:

1. Start at the URL you pass (typically `https://github.com`).
2. Search for the repository (click search bar → type → Enter).
3. Click the correct repo in results.
4. Open the **Releases** section (sidebar or header link).
5. Click the **Latest** stable release; use small scrolls (amount 1–2) **within** that release to read notes and **Assets** — avoid scrolling the release list past the target version.
6. Read the latest **stable** release from the page (skipping pre-releases) and return all eight JSON fields.

Heuristics for this flow live in the system prompt (`agent/prompts.py`), not in selector-based code.

## Design (short)

- **One action per turn** — click, type, press_key, scroll, wait, or `done` with extracted fields.
- **0–1000 normalized coordinates** — the model proposes `(x, y)`; Playwright maps to pixel space from viewport size.
- **No selectors** — the agent only sees PNG screenshots; GitHub layout hints live in the system prompt.
- **Dual vision backends** — Ollama (cloud or local) by default; Gemini as optional fallback.

## Project layout

```
navigate.py           # CLI entrypoint
agent/
  browser.py          # Playwright wrapper (no selectors)
  loop.py             # Screenshot → decide → act loop
  schema.py           # Pydantic action models and JSON schema
  prompts.py          # System prompt for vision models
  action_parse.py     # Action JSON parsing and normalization
  vision_parse.py     # Parse-with-retry orchestration for vision backends
  defaults.py         # Shared model/host defaults
  errors.py           # Shared vision exception types
  vision.py           # create_vision_client() factory + VisionClient protocol
  ollama_client.py    # Ollama Cloud / local backend
  gemini_client.py    # Gemini structured-output backend
docs/                 # Architecture, phases, iteration log
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), progress: [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md).

## Tested with

### v1 (2026-05-30)

```bash
python navigate.py \
  --url "https://github.com" \
  --prompt "search for facebook/react and get the latest release info" \
  --headed --debug
```

- **Python**: 3.14.0
- **Provider / model**: Ollama Cloud, `qwen3-vl:235b-cloud`
- **Steps**: 9 (search → repo → releases → `done`)
- **Output**: `facebook/react`, stable release `19.2.6`, tag `v19.2.6`, author `eps1lon`
- **Commit**: `b9f977d`

### v2 (2026-05-30)

```bash
python -u navigate.py \
  --url "https://github.com" \
  --prompt "search for facebook/react and get the latest release info" \
  --headed --debug
```

- **Python**: 3.14.0
- **Provider / model**: Ollama Cloud, `qwen3-vl:235b-cloud`
- **Steps**: 9 (search → repo → releases → scroll ×2 → `done`)
- **Wall-clock budget**: 420s default in `agent/loop.py`
- **Output**: `facebook/react`, stable release **19.2.6**, tag `v19.2.6`, author `eps1lon`, non-empty `release_notes` and Source code zip/tar.gz in `downloads`

```json
{
  "repository": "facebook/react",
  "latest_release": "19.2.6 (May 6th, 2026)",
  "version": "19.2.6",
  "tag": "v19.2.6",
  "author": "eps1lon",
  "published_at": "May 6th, 2026",
  "release_notes": "React Server Components\n* Type hardening and performance improvements\n[#36425](https://github.com/facebook/react/pull/36425) by @eps1lon and @unstubbable",
  "downloads": [
    { "name": "Source code (zip)", "url": "https://github.com/facebook/react/archive/refs/tags/v19.2.6.zip" },
    { "name": "Source code (tar.gz)", "url": "https://github.com/facebook/react/archive/refs/tags/v19.2.6.tar.gz" }
  ]
}
```

Ollama occasionally returns malformed action JSON mid-run (truncated responses, unquoted keys); the parser salvages or retries and the run can still succeed — see [docs/BACKLOG.md](docs/BACKLOG.md) for remaining normalization ideas.

## Limitations

Vision-driven navigation with an eight-field release snapshot (v2). Not included — see [docs/BACKLOG.md](docs/BACKLOG.md) for planned extensions:

- **Release notes** — transcribed from screenshots; long changelogs may be **partial** even after scrolling.
- **Download URLs** — vision-extracted from the Assets section; may be incomplete or imperfect if links are off-screen (anti-hallucination rules omit guessed URLs).
- **Stable-release selection** — the model can pick a stable entry that is not the newest semver; verify against GitHub when correctness matters.
- **Ollama JSON flakiness** — malformed action JSON is retried/salvaged; stderr may show `[vision:ollama] invalid JSON` even on successful runs.
- **Wall-clock budget** — default **420s** loop cap (Ollama Cloud inference is slow; v2 adds scroll steps for notes and Assets).
- **Direct repo targeting** — no `--repo owner/name` (or repo URL) flag; you start from `--url` and describe the goal in `--prompt`.
- **Open-ended queries** — prompts are aimed at latest-release lookup, not tasks like comparing releases, listing key features, or summarizing changelog highlights.

## Troubleshooting

| Issue | What to check |
|---|---|
| `OLLAMA_API_KEY is not set` | Required for `https://ollama.com`; create a key at ollama.com/settings/keys |
| Cannot connect to Ollama | Cloud: key and model name; local: `ollama serve` running, `OLLAMA_HOST` matches |
| Model not found | Pull locally (`ollama pull <model>`) or pick a cloud-available tag |
| Invalid action JSON | Auto-retry once; truncated JSON salvaged when possible; use `--debug` for `[vision:ollama] invalid JSON` lines and `screenshots/` |
| Playwright errors | `playwright install chromium` inside the venv |
| Max steps / timeout | Default 420s wall clock; use `--debug`, inspect screenshots; raise `--max-steps` if needed |
| Gemini rate limit | Switch to `--provider ollama` or wait and retry |
