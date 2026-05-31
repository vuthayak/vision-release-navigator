#!/usr/bin/env python3
"""CLI entrypoint for the vision-driven GitHub release navigator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from agent.browser import Browser
from agent.loop import AgentLoopError, run_agent_loop
from agent.defaults import DEFAULT_GEMINI_MODEL, DEFAULT_OLLAMA_HOST, DEFAULT_OLLAMA_MODEL
from agent.vision import VisionClientError, create_vision_client


class ConfigError(Exception):
    """Missing or invalid configuration."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Navigate a website with a vision model and extract GitHub release metadata.",
    )
    parser.add_argument("--url", required=True, help="Starting page URL (e.g. https://github.com)")
    parser.add_argument("--prompt", required=True, help="Natural-language navigation goal")
    parser.add_argument(
        "--provider",
        choices=["ollama", "gemini"],
        default=os.environ.get("VISION_PROVIDER", "ollama"),
        help="Vision backend (default: ollama, or VISION_PROVIDER env)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Model id (default: {DEFAULT_OLLAMA_MODEL} for ollama, {DEFAULT_GEMINI_MODEL} for gemini)",
    )
    parser.add_argument(
        "--ollama-host",
        default=os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST),
        help=f"Ollama base URL (default: {DEFAULT_OLLAMA_HOST} for cloud; use http://localhost:11434 for local)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=30,
        help="Maximum agent loop iterations (default: 30)",
    )
    parser.add_argument(
        "--time-budget",
        type=float,
        default=420.0,
        metavar="SECONDS",
        help="Wall-clock time limit for the agent loop (default: 420)",
    )
    visibility = parser.add_mutually_exclusive_group()
    visibility.add_argument("--headless", action="store_true", help="Run browser headless")
    visibility.add_argument("--headed", action="store_true", help="Show browser window (default)")
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Also write final JSON to this file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save step screenshots and actions under screenshots/",
    )
    return parser


def _resolve_model(provider: str, cli_model: str | None) -> str:
    if cli_model:
        return cli_model
    if provider == "ollama":
        return os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    return DEFAULT_GEMINI_MODEL


def _emit_result(payload: dict[str, Any], output_path: str | None) -> None:
    text = json.dumps(payload, indent=2)
    print(text)  # stdout is the primary contract for piping / CI.
    if output_path:
        Path(output_path).write_text(text + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    provider = args.provider.strip().lower()
    model = _resolve_model(provider, args.model)

    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    ollama_api_key = os.environ.get("OLLAMA_API_KEY", "").strip()

    headless = bool(args.headless)
    debug_dir = Path("screenshots") if args.debug else None

    try:
        # Wire vision backend from env + CLI flags.
        vision = create_vision_client(
            provider,
            model=model,
            api_key=api_key or None,
            ollama_host=args.ollama_host,
            ollama_api_key=ollama_api_key or None,
        )
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    with Browser(headless=headless) as browser:
        browser.goto(args.url)
        done = run_agent_loop(
            browser,
            vision,
            user_prompt=args.prompt,
            max_steps=args.max_steps,
            time_budget_s=args.time_budget,
            debug_dir=debug_dir,
            debug_vision=args.debug,
        )

    # Strip internal reasoning field before emitting the public release JSON.
    payload = done.model_dump(exclude={"reasoning"})
    _emit_result(payload, args.output)
    return 0


def main() -> None:
    load_dotenv()
    parser = _build_parser()
    args = parser.parse_args()
    try:
        code = run(args)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    except VisionClientError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    except AgentLoopError as exc:
        print(f"Agent failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(code)


if __name__ == "__main__":
    main()
