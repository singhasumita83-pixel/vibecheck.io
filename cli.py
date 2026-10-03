#!/usr/bin/env python3
"""
cli.py – VibeCheck command-line interface
==========================================

Usage
-----
  python cli.py <screenshot.png> [options]

Options
-------
  --persona TEXT          User persona for the analysis  (e.g. "mobile user")
  --goal TEXT             User goal / task               (e.g. "complete signup")
  --json                  Print raw JSON result to stdout
  --md <report.md>        Write Markdown report to FILE
  --fail-on LEVEL         Exit 1 if any finding is at or above LEVEL
                          Choices: critical | high | medium | low
                          Default: none (always exit 0)

Environment variables (or .env file)
-------------------------------------
  LLM_BASE_URL    Base URL of the OpenAI-compatible endpoint
  LLM_API_KEY     API key for the endpoint
  VLM_MODEL       Vision model name
  VERIFIER_MODEL  Verifier / critique model name

Examples
--------
  python cli.py demo.png --fail-on high
  python cli.py ui.png --persona "new user" --goal "sign up" --md report.md
  python cli.py ui.png --json | jq .summary
"""

import argparse
import json
import os
import sys
from pathlib import Path

# ─── Environment setup (must happen before any analyzer import) ───────────────
from dotenv import load_dotenv
load_dotenv()

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEV_MARKS = {"Critical": "■", "High": "●", "Medium": "◐", "Low": "○"}


# ─── Argument parsing ─────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vibecheck",
        description="VibeCheck – AI UX auditor for screenshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("screenshot", help="Path to the screenshot PNG/JPG to audit")
    p.add_argument("--persona", default="", metavar="TEXT",
                   help="User persona for context (e.g. 'mobile user')")
    p.add_argument("--goal", default="", metavar="TEXT",
                   help="User goal (e.g. 'complete signup')")
    p.add_argument("--json", action="store_true", dest="output_json",
                   help="Print raw JSON result to stdout")
    p.add_argument("--md", metavar="FILE", default=None,
                   help="Write Markdown report to FILE")
    p.add_argument(
        "--fail-on",
        metavar="LEVEL",
        default=None,
        choices=["critical", "high", "medium", "low"],
        dest="fail_on",
        help="Exit with code 1 if any finding is at or above this severity",
    )
    return p


# ─── Pretty table printer ─────────────────────────────────────────────────────

def _col(s: str, width: int) -> str:
    s = str(s)
    return s[:width].ljust(width)


def print_table(findings: list) -> None:
    cols = [
        ("#",        4),
        ("Sev",      8),
        ("Category", 20),
        ("Title",    44),
        ("Location", 28),
    ]
    header = "  ".join(_col(name, w) for name, w in cols)
    sep = "  ".join("-" * w for _, w in cols)
    print(header)
    print(sep)

    for idx, f in enumerate(findings, start=1):
        sev = f.get("severity", "")
        mark = SEV_MARKS.get(sev, "·")
        cat = f.get("category", "")
        title = f.get("title", "")

        loc_parts = []
        loc = f.get("code_location")
        if loc and isinstance(loc, dict):
            loc_parts.append(f"{loc.get('file','?')}:{loc.get('line_start','?')}")
        elif f.get("location") and isinstance(f["location"], dict):
            lx = round(f["location"].get("x", 0) * 100)
            ly = round(f["location"].get("y", 0) * 100)
            loc_parts.append(f"x={lx}% y={ly}%")
        location_str = loc_parts[0] if loc_parts else ""

        row_vals = [str(idx), f"{mark} {sev}", cat, title, location_str]
        print("  ".join(_col(v, w) for v, (_, w) in zip(row_vals, cols)))


def print_summary(result: dict) -> None:
    summary = result.get("summary") or {}
    counts = summary.get("counts") or {}
    scores = summary.get("scores") or {}

    c = counts.get("critical", 0)
    h = counts.get("high", 0)
    m = counts.get("medium", 0)
    lo = counts.get("low", 0)
    total = c + h + m + lo

    print(f"\n{total} issues  ■ {c} critical  ● {h} high  ◐ {m} medium  ○ {lo} low")

    if scores:
        parts = []
        for cat, score in scores.items():
            parts.append(f"{cat}: {score}")
        print("Scores  " + "  ·  ".join(parts))


# ─── Exit-code logic ──────────────────────────────────────────────────────────

def should_fail(findings: list, fail_on: str | None) -> bool:
    if not fail_on:
        return False
    threshold = SEVERITY_ORDER[fail_on.lower()]
    for f in findings:
        sev = (f.get("severity") or "").lower()
        if sev in SEVERITY_ORDER and SEVERITY_ORDER[sev] <= threshold:
            return True
    return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Validate input file
    img_path = Path(args.screenshot)
    if not img_path.exists():
        print(f"error: file not found: {img_path}", file=sys.stderr)
        return 2
    if not img_path.is_file():
        print(f"error: not a file: {img_path}", file=sys.stderr)
        return 2

    # Read image
    try:
        image_bytes = img_path.read_bytes()
    except OSError as e:
        print(f"error: cannot read file: {e}", file=sys.stderr)
        return 2

    # Run pipeline
    try:
        from analyzer.pipeline import AnalysisPipeline
        pipeline = AnalysisPipeline()
        result = pipeline.analyze(
            image_bytes=image_bytes,
            persona=args.persona,
            goal=args.goal,
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        # Catch connectivity / model errors
        msg = str(e)
        if "connect" in msg.lower() or "timeout" in msg.lower() or "connection" in msg.lower():
            print(f"error: cannot reach model endpoint – {e}", file=sys.stderr)
            return 3
        print(f"error: analysis failed – {e}", file=sys.stderr)
        return 1

    result_dict = result.model_dump()
    findings = result_dict.get("findings") or []

    # ── JSON output ────────────────────────────────────────────────────────────
    if args.output_json:
        print(json.dumps(result_dict, indent=2))
        return 0

    # ── Pretty table ───────────────────────────────────────────────────────────
    print_table(findings)
    print_summary(result_dict)

    # ── Markdown report ────────────────────────────────────────────────────────
    if args.md:
        try:
            from analyzer.report_md import build_markdown
            md_text = build_markdown(result_dict)
            md_path = Path(args.md)
            md_path.write_text(md_text, encoding="utf-8")
            print(f"\nMarkdown report written to: {md_path}")
        except Exception as e:
            print(f"warning: could not write markdown report: {e}", file=sys.stderr)

    # ── Exit code ──────────────────────────────────────────────────────────────
    if should_fail(findings, args.fail_on):
        print(
            f"\nFAIL: findings at or above '{args.fail_on}' severity were found.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
