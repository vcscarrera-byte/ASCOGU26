#!/usr/bin/env python3
"""CLI: export collected tweets to CSV or JSONL."""

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.config import get_db_path, get_exports_dir
from src.db import create_tables, get_connection
from src.export import export_tweets_csv, export_tweets_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def parse_date(value: str) -> str | None:
    if value == "all":
        return None
    if value == "yesterday":
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    if value == "today":
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    datetime.strptime(value, "%Y-%m-%d")
    return value


def main():
    parser = argparse.ArgumentParser(description="Export tweets to CSV/JSONL")
    parser.add_argument("--date", default="all", help="Date or 'all'")
    parser.add_argument("--format", choices=["csv", "jsonl", "both"], default="csv")
    args = parser.parse_args()

    date = parse_date(args.date)
    suffix = date or "all"
    exports_dir = get_exports_dir()
    conn = get_connection(get_db_path())
    create_tables(conn)

    if args.format in ("csv", "both"):
        path = exports_dir / f"tweets_{suffix}.csv"
        count = export_tweets_csv(conn, path, date)
        print(f"Exported {count} tweets to {path}")

    if args.format in ("jsonl", "both"):
        path = exports_dir / f"tweets_{suffix}.jsonl"
        count = export_tweets_jsonl(conn, path, date)
        print(f"Exported {count} tweets to {path}")

    conn.close()


if __name__ == "__main__":
    main()
