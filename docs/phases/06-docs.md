# Phase 06 — Documentation

## Goal

Replace the placeholder `README.md` with a complete, reviewer-ready document. This is a take-home, so the README is part of the deliverable, not an afterthought.

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

## Deliverables

A `README.md` covering:

1. **What it does** — one-paragraph elevator pitch.
2. **Demo** — embed an animated GIF or at minimum a captioned screenshot from `screenshots/`.
3. **Setup**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   cp .env.example .env  # OLLAMA_HOST, OLLAMA_API_KEY, OLLAMA_MODEL
   ```
4. **Usage** — the canonical command:
   ```bash
   python navigate.py --url "https://github.com" \
     --prompt "search for openclaw and get the current release and related tags"
   ```
   plus 2–3 more example prompts on different repos.
5. **Output schema** — the JSON contract.
6. **Design notes** — why coordinates over selectors, why one action per turn, 0–1000 convention, the no-progress heuristic.
7. **Project layout** — quick tree.
8. **Known limitations** — pull from [BACKLOG.md](../BACKLOG.md): no auth, no captcha, only top release, single tab.
9. **Troubleshooting** — Ollama Cloud auth, local Ollama not running, model not pulled, Playwright not installed, max steps, etc.
10. **Development docs** — link to `docs/IMPLEMENTATION.md` for contributors.

## Tasks

- [x] Draft README sections above (setup, usage, output, design, layout, troubleshooting).
- [x] Sync `docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION.md`, and phase files with current code.
- [ ] Run the canonical command, screenshot the final terminal output and an interesting mid-flow browser frame, save under `screenshots/demo/` (git-tracked, **not** ignored — adjust `.gitignore` accordingly).
- [ ] Confirm every command in the README actually works on a fresh checkout.
- [x] Add a "Tested with" block: Python version, OS, Ollama model id, commit SHA.

## Acceptance criteria

- Reviewer can go from `git clone` to a working JSON output in under 5 minutes by following only the README.
- All code blocks are copy-pasteable (no shell-prompt prefixes like `$`).
- Links to other docs (`docs/ARCHITECTURE.md`, etc.) all resolve.

## Dependencies

- Phases 01–05 done.

## Risks

- Tutorial drift: easy to forget a step that "just works" on your machine. Mitigate by checking out into a fresh `/tmp` clone and running through it before finalizing.

## Notes

- Keep the design-notes section short and concrete — reviewers care more about *why* than *what*. The architecture deep-dive belongs in `docs/ARCHITECTURE.md`.
