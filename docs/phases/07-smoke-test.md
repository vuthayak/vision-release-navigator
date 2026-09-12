# Phase 07 — Smoke test & iteration

## Goal

Validate the tool end-to-end on real GitHub repositories and use the findings to harden prompts, raise step caps, and lock dependency versions. This phase is where you actually *iterate*.

## Status

- **State**: Cancelled (formal matrix out of scope for this iteration)
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

Iteration happened via ad-hoc `--headed --debug` runs and bug fixes logged in [ITERATION-LOG.md](../ITERATION-LOG.md). The 5-repo test matrix and `smoke-results.md` were explicitly dropped.

## Deliverables

- A `smoke-results.md` table (or inline section in `ITERATION-LOG.md`) recording each test repo, the prompt used, the resulting JSON, whether it matched ground-truth, and how many steps it took.
- A pinned `requirements.txt` (exact versions of the dependencies that produced a passing run).
- Any prompt or loop adjustments made during the iteration loop, captured as separate entries in [ITERATION-LOG.md](../ITERATION-LOG.md).

## Test matrix

Run the canonical command (varying the search target) against repos that exercise different shapes of "release":

| # | Target | Why | Prompt |
|---|---|---|---|
| 1 | `facebook/react` | Many releases, semver tags, well-known | "search for facebook/react and get the latest release info" |
| 2 | `microsoft/vscode` | Monthly tagged releases, long titles | "find microsoft vscode and tell me the most recent release" |
| 3 | `cli/cli` (GitHub CLI) | Short repo name in search, conflicts possible | "search for github cli and report the latest release" |
| 4 | A repo with **no** releases (e.g. a tiny one-off) | Negative case — does the agent emit blank `done` or get stuck? | "search for {repo} and get release info" |
| 5 | A repo whose name overlaps a popular topic | Ambiguous search results | "search for {repo} and grab the newest release" |

For each row, record: extracted JSON, ground-truth JSON (manually verified), match/mismatch per field, total steps, total wall-clock, inference time per step (Ollama), link to debug screenshots.

## Tasks

- [ ] Build the test matrix above as a `smoke-results.md` file with empty result cells.
- [ ] Run row 1; if it fails, file the failure in `ITERATION-LOG.md`, adjust prompt/loop, re-run, repeat until pass.
- [ ] Repeat for rows 2–5.
- [ ] Once all green, lock dependency versions: `pip freeze | grep -iE "playwright|ollama|pydantic|python-dotenv" > /tmp/locks` then update `requirements.txt`.
- [ ] If any iteration touched the system prompt, copy the final version into `ARCHITECTURE.md`'s "System prompt" section so it doesn't drift.

## Iteration playbook

When a smoke test fails, work through these in order:

1. **Read the last 3 screenshots + actions** in `screenshots/`. Where did the model go wrong?
2. **Misclick?** Tighten the system prompt's coordinate guidance, or add a hint about the GitHub layout (without naming selectors).
3. **Got lost in a sub-page?** Add a "if you're not where you expect, look for a back arrow or top-left logo" line to the prompt.
4. **Stopped early with blank fields?** Strengthen the stop-condition clause: "do not emit `done` unless you can read the version number from the page."
5. **Hit `max_steps`?** Raise the cap by 5, but only after confirming the model is making progress (URL/screenshot changing) — otherwise fix the loop, not the cap.
6. **Token usage ballooning?** Trim history length or `reasoning` cap in the history formatter.

## Acceptance criteria

- At least **3 of 5** test rows produce correct JSON on the first run after iteration settles. (The negative case may legitimately exit non-zero; that still counts as "correct behavior".)
- Median step count ≤ 12 across passing runs.
- No row takes > 90 s of wall clock (may need GPU or smaller model if CPU-bound).
- Final `requirements.txt` is pinned and reproduces the smoke results on a fresh venv.

## Dependencies

- Phase 03 Ollama migration complete.
- All previous phases done.

## Risks

- **Local compute**: each step is an Ollama vision call with an image. Five test rows × ~10 steps × ~3 iterations adds up on CPU — prefer a pulled vision model sized for your hardware.
- **Flakiness**: GitHub's UI can change. A smoke result that passes today may fail next month. The README's "Tested with" block plus dated entries in `ITERATION-LOG.md` make drift easy to spot.
- **GitHub rate-limiting / bot detection**: aggressive runs may trigger a soft block. Space runs out, set a realistic user agent (phase 02), and avoid headless mode for early iteration (more human-like).

## Notes

- This phase is intentionally where most of the "interesting" engineering happens. Budget 1.5–2× the time you spent on phases 02–05 combined.
- When you finish, sketch one paragraph in the README about what you learned — that often becomes the most compelling part of the project narrative.
