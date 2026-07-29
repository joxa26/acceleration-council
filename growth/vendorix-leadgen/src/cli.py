"""Entry point: python -m src.cli --limit 15"""
import argparse
import os
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from .agent import research_leads

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    load_dotenv(ROOT / ".env")

    parser = argparse.ArgumentParser(description="Research leads for Vendorix")
    parser.add_argument("--limit", type=int, default=15, help="Max new leads to find this run")
    parser.add_argument("--icp", type=Path, default=ROOT / "config" / "icp.yaml")
    parser.add_argument(
        "--sink",
        choices=["notion", "csv"],
        default=None,
        help="Where to write leads. Defaults to notion if NOTION_API_KEY and "
        "NOTION_DATABASE_ID are set, otherwise csv.",
    )
    parser.add_argument(
        "--output", type=Path, default=ROOT / "output" / "leads.csv",
        help="CSV path, only used with --sink csv",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set (check your .env or environment)")

    notion_key = os.environ.get("NOTION_API_KEY")
    notion_db = os.environ.get("NOTION_DATABASE_ID")
    sink = args.sink or ("notion" if notion_key and notion_db else "csv")

    icp_text = args.icp.read_text()
    client = anthropic.Anthropic()

    if sink == "notion":
        if not (notion_key and notion_db):
            sys.exit("--sink notion requires NOTION_API_KEY and NOTION_DATABASE_ID")
        from . import notion_store as store
        existing_keys = store.load_existing_keys(notion_key, notion_db)
        print(f"{len(existing_keys)} leads already in Notion. Researching up to {args.limit} new ones...")
        leads = research_leads(client, icp_text, args.limit, existing_keys)
        added = store.append_leads(notion_key, notion_db, leads)
        print(f"Found {len(leads)} candidates, added {added} new leads to Notion")
    else:
        from . import storage
        existing_keys = storage.load_existing_keys(args.output)
        print(f"{len(existing_keys)} leads already on file. Researching up to {args.limit} new ones...")
        leads = research_leads(client, icp_text, args.limit, existing_keys)
        added = storage.append_leads(args.output, leads)
        print(f"Found {len(leads)} candidates, added {added} new leads to {args.output}")

    if added < len(leads):
        print(f"({len(leads) - added} were duplicates and were skipped)")


if __name__ == "__main__":
    main()
