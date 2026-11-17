"""CLI: uv run --env-file .env python -m agent "Brand Name"   (a website like brand.com also works)"""
import argparse
import asyncio
import logging
import os
import sys

from agent.pipeline import run_company
from agent.stages.render import write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Find where Flowcode could help a company, with cited sources.")
    parser.add_argument("company", help='company name or website, e.g. "Acme Foods" or acmefoods.com')
    args = parser.parse_args()

    missing = [k for k in ("EXA_API_KEY", "ANTHROPIC_API_KEY") if not os.environ.get(k)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}. Put them in .env and run: uv run --env-file .env python -m agent \"Brand\"")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # hide one log line per API request
    report = asyncio.run(run_company(args.company))
    md_path, json_path = write_outputs(report)
    s = report.stats
    print(f"\nWrote {md_path} and {json_path}")
    print(f"{len(report.opportunities)} opportunities | {s.search_calls} searches | "
          f"{s.input_tokens:,} in / {s.output_tokens:,} out tokens | ${s.cost_usd:.3f} | {s.seconds:.0f}s")


if __name__ == "__main__":
    main()
