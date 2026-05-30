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
   OLLAMA_MODEL=qwen2.5vl:3b
   ```

**Local Ollama** (alternative):

```bash
ollama serve   # if not already running
ollama pull qwen2.5vl:3b
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
  --prompt "find microsoft vscode and tell me the most recent release" \
  --model qwen3-vl:235b-cloud
```

| Flag | Default | Purpose |
|---|---|---|
| `--provider` | `ollama` | `ollama` or `gemini` |
| `--model` | `qwen2.5vl:3b` (ollama) | Vision model id |
| `--ollama-host` | `https://ollama.com` | Ollama API base URL |
| `--max-steps` | 25 | Agent loop iteration cap |
| `--headed` / `--headless` | headed | Browser visibility |
| `--output PATH` | — | Also write final JSON to file |
| `--debug` | off | Save `screenshots/step_*.png` and action JSON |

## Output

```json
{
  "repository": "owner/repo",
  "latest_release": "Release title",
  "version": "1.0.0",
  "tag": "v1.0.0",
  "author": "github_username"
}
```

Printed to stdout (and optionally `--output`). Logs and debug lines go to stderr.

## How it navigates

The agent does not follow a hardcoded script. Each turn it screenshots the viewport, asks the vision model for **one** action, executes it, and repeats until it emits `done`.

For GitHub release tasks, the intended flow is:

1. Start at the URL you pass (typically `https://github.com`).
2. Search for the repository (click search bar → type → Enter).
3. Click the correct repo in results.
4. Open the **Releases** section (sidebar or header link).
5. Read the latest **stable** release from the page (skipping pre-releases) and return the five JSON fields.

Heuristics for this flow live in the system prompt (`agent/schema.py`), not in selector-based code.

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
  schema.py           # Action schema, system prompt, JSON parsing
  vision.py           # create_vision_client() factory
  ollama_client.py    # Ollama Cloud / local backend
  gemini_client.py    # Gemini structured-output backend
docs/                 # Architecture, phases, iteration log
```

Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), progress: [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md).

## Tested with

Verified end-to-end on macOS (2026-05-30):

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

## Limitations

No private-repo auth, captcha handling, or multi-tab support. Extraction targets the latest stable release visible on the releases page, not full changelog mining. See [docs/BACKLOG.md](docs/BACKLOG.md).

## Troubleshooting

| Issue | What to check |
|---|---|
| `OLLAMA_API_KEY is not set` | Required for `https://ollama.com`; create a key at ollama.com/settings/keys |
| Cannot connect to Ollama | Cloud: key and model name; local: `ollama serve` running, `OLLAMA_HOST` matches |
| Model not found | Pull locally (`ollama pull <model>`) or pick a cloud-available tag |
| Invalid action JSON | Usually auto-retries once; re-run with `--debug` to inspect `screenshots/` |
| Playwright errors | `playwright install chromium` inside the venv |
| Max steps / timeout | Use `--debug`, inspect screenshots; tighten prompt or raise `--max-steps` |
| Gemini rate limit | Switch to `--provider ollama` or wait and retry |
