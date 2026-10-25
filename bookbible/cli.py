"""Command line interface for the book bible auditor."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .audit import audit
from .bible import parse_bible
from .llm import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
    LLMError,
    build_payload,
    resolve_api_key,
    review,
)
from .manuscript import load_text
from .report import render_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bookbible",
        description=(
            "Audit a manuscript against a series bible (CSV or JSON) and write "
            "a Markdown continuity report."
        ),
    )
    parser.add_argument("manuscript", help="manuscript file (.txt or .md)")
    parser.add_argument(
        "--bible",
        required=True,
        dest="bible",
        help="series bible file (.csv or .json)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="output Markdown report path (default: print to stdout)",
    )
    parser.add_argument(
        "--min-repeat",
        type=int,
        default=3,
        help="minimum occurrences to flag a repeated phrase (default: 3)",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="add an LLM second opinion using an OpenAI-compatible endpoint",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"OpenAI-compatible base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"chat model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="optional API key (also read from BOOKBIBLE_API_KEY env var)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"LLM request timeout in seconds (default: {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    manuscript_path = Path(args.manuscript)
    bible_path = Path(args.bible)
    if not manuscript_path.is_file():
        parser.error(f"manuscript not found: {manuscript_path}")
    if not bible_path.is_file():
        parser.error(f"bible not found: {bible_path}")
    if args.bible.lower().endswith((".csv", ".json")) is False:
        parser.error("bible must be a .csv or .json file")

    try:
        bible = parse_bible(bible_path)
    except (ValueError, KeyError) as exc:
        parser.error(f"cannot parse bible: {exc}")

    text = load_text(str(manuscript_path))
    result = audit(bible, text, repeat_threshold=max(2, args.min_repeat))

    llm_section = ""
    if args.llm:
        api_key = resolve_api_key(args.api_key)
        payload = build_payload(bible, result, text)
        try:
            content = review(
                payload,
                base_url=args.base_url,
                model=args.model,
                api_key=api_key,
                timeout=args.timeout,
            )
            llm_section = content
        except LLMError as exc:
            llm_section = (
                f"> LLM second opinion skipped: {exc}\n>\n"
                "> Start a local model server (for example `ollama serve`) and retry, "
                "or pass `--base-url` pointing at another OpenAI-compatible endpoint."
            )

    report = render_report(
        result,
        manuscript_path=str(manuscript_path),
        bible_path=str(bible_path),
        repeat_threshold=max(2, args.min_repeat),
        llm_section=llm_section,
    )

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        summary = result.counts_by_severity()
        print(
            f"Wrote {args.output}: "
            f"{summary.get('high', 0)} high, {summary.get('medium', 0)} medium, "
            f"{summary.get('info', 0)} info findings."
        )
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
