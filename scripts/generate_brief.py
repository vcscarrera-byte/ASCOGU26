#!/usr/bin/env python3
"""CLI: generate daily brief (EN + PT-BR) via Claude API."""

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.config import get_db_path
from src.db import create_tables, get_connection
from src.summarizer import generate_both_briefs, generate_brief

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def parse_date(value: str) -> str:
    if value == "yesterday":
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    if value == "today":
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    datetime.strptime(value, "%Y-%m-%d")
    return value


def main():
    parser = argparse.ArgumentParser(description="Generate daily brief")
    parser.add_argument("--date", required=True, help="Date (YYYY-MM-DD, 'yesterday', 'today')")
    parser.add_argument("--lang", choices=["en", "pt", "both"], default="both",
                        help="Language: 'en', 'pt', or 'both'")
    args = parser.parse_args()

    date_str = parse_date(args.date)
    conn = get_connection(get_db_path())
    create_tables(conn)

    if args.lang == "both":
        print(f"Generating EN + PT-BR briefs for {date_str}...")
        results = generate_both_briefs(conn, date_str)
        for lang, text in results.items():
            print(f"\n{'='*60}")
            print(f"  {lang.upper()} Brief ({len(text)} chars)")
            print(f"{'='*60}")
            print(text[:500] + "..." if len(text) > 500 else text)
    else:
        print(f"Generating {args.lang.upper()} brief for {date_str}...")
        text = generate_brief(conn, date_str, args.lang)
        print(text)

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
