#!/usr/bin/env python3
"""CLI: run a daily tweet collection."""

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.collector import collect_daily

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def parse_date(value: str) -> str:
    """Parse date string or 'yesterday'/'today' into YYYY-MM-DD."""
    if value == "yesterday":
        return (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    if value == "today":
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Validate format
    datetime.strptime(value, "%Y-%m-%d")
    return value


def main():
    parser = argparse.ArgumentParser(description="Collect tweets for a given date")
    parser.add_argument(
        "--date",
        required=True,
        help="Date to collect (YYYY-MM-DD, 'yesterday', or 'today')",
    )
    args = parser.parse_args()

    date_str = parse_date(args.date)
    start_time = f"{date_str}T00:00:00Z"

    # end_time must not be in the future (X API rejects it)
    end_time_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
    now = datetime.now(timezone.utc)
    if end_time_dt > now:
        # For today or future dates, use 10 seconds ago to avoid edge cases
        end_time_dt = now - timedelta(seconds=10)
    end_time = end_time_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Collecting tweets for {date_str} ({start_time} -> {end_time})")
    stats = collect_daily(date_str, start_time, end_time)

    print(f"\nDone!")
    print(f"  Queries run: {stats['queries']}")
    print(f"  Tweets fetched: {stats['tweets_fetched']}")
    print(f"  New tweets stored: {stats['tweets_new']}")
    print(f"  Collection run ID: {stats['run_id']}")


if __name__ == "__main__":
    main()
