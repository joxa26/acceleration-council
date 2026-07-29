"""Entry point: python -m src.cli --limit 15"""
import argparse
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from .agent import research_leads
from .storage import append_leads, load_existing_keys

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Research LinkedIn leads for AI Invoice Capturer"
    )
    parser.add_argument("--limit", type=int, default=15, help="Max new leads to find this run")
    parser.add_argument("--icp", type=Path, default=ROOT / "config" / "icp.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "leads.csv")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set (check your .env or environment)")

    icp_text = args.icp.read_text()
    client = anthropic.Anthropic()

    existing_keys = load_existing_keys(args.output)
    print(f"{len(existing_keys)} leads already on file. Researching up to {args.limit} new ones...")

    leads = research_leads(client, icp_text, args.limit, existing_keys)
    added = append_leads(args.output, leads)

    print(f"Found {len(leads)} candidates, added {added} new leads to {args.output}")
    if added < len(leads):
        print(f"({len(leads) - added} were duplicates of existing rows and were skipped)")


if __name__ == "__main__":
    main()
