#!/usr/bin/env python3
"""CLI: compute daily aggregate metrics."""

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.aggregator import compute_daily_metrics, get_available_dates
from src.config import get_db_path
from src.db import create_tables, get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def parse_date(value: str) -> str:
    if value == "yesterday":
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    if value == "today":
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if value == "all":
        return "all"
    datetime.strptime(value, "%Y-%m-%d")
    return value


def main():
    parser = argparse.ArgumentParser(description="Compute daily aggregate metrics")
    parser.add_argument(
        "--date",
        required=True,
        help="Date (YYYY-MM-DD, 'yesterday', 'today', or 'all')",
    )
    args = parser.parse_args()

    date_str = parse_date(args.date)
    conn = get_connection(get_db_path())
    create_tables(conn)

    if date_str == "all":
        dates = get_available_dates(conn)
        print(f"Computing metrics for {len(dates)} dates...")
        for d in dates:
            summary = compute_daily_metrics(conn, d)
            print(f"  {d}: {summary['total_tweets']} tweets, {summary['total_engagement']} engagement")
    else:
        summary = compute_daily_metrics(conn, date_str)
        print(f"Metrics for {date_str}:")
        print(f"  Total tweets: {summary['total_tweets']}")
        print(f"  Total engagement: {summary['total_engagement']}")
        print(f"  Unique authors: {summary['unique_authors']}")

    conn.close()


if __name__ == "__main__":
    main()
