#!/usr/bin/env python3
"""Collect tweets for all dates since the last successful extraction until today."""

import logging
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))

from src.collector import collect_daily
from src.config import get_db_path
from src.db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_last_collection_date(conn) -> str | None:
    """Return the end_time date of the most recent completed collection run."""
    row = conn.execute(
        """SELECT MAX(DATE(end_time)) as last_date
           FROM collection_runs
           WHERE status = 'completed'"""
    ).fetchone()
    return row["last_date"] if row and row["last_date"] else None


def dates_to_collect(last_date_str: str) -> list[str]:
    """Generate list of dates from the day after last_date until today (UTC)."""
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    today = datetime.now(timezone.utc).date()

    dates = []
    current = last_date + timedelta(days=1)
    while current <= today:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return dates


def main():
    db_path = get_db_path()
    conn = get_connection(db_path)

    last_date = get_last_collection_date(conn)
    conn.close()

    if not last_date:
        print("No previous collection runs found. Use scripts/collect.py --date YYYY-MM-DD for the first run.")
        sys.exit(1)

    print(f"Last successful collection: {last_date}")

    pending_dates = dates_to_collect(last_date)

    if not pending_dates:
        print("Already up to date! No new dates to collect.")
        return

    print(f"Dates to collect: {', '.join(pending_dates)}")
    print()

    total_fetched = 0
    total_new = 0

    for date_str in pending_dates:
        start_time = f"{date_str}T00:00:00Z"

        end_time_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        ) + timedelta(days=1)
        now = datetime.now(timezone.utc)
        if end_time_dt > now:
            end_time_dt = now - timedelta(seconds=10)
        end_time = end_time_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"--- Collecting {date_str} ({start_time} -> {end_time}) ---")

        try:
            stats = collect_daily(date_str, start_time, end_time)
            print(f"  Queries: {stats['queries']}")
            print(f"  Fetched: {stats['tweets_fetched']}")
            print(f"  New: {stats['tweets_new']}")
            total_fetched += stats["tweets_fetched"]
            total_new += stats["tweets_new"]
        except Exception as e:
            logger.error(f"Failed to collect {date_str}: {e}")
            print(f"  ERROR: {e}")
            print("  Stopping to avoid gaps. Fix the issue and re-run.")
            sys.exit(1)

        print()

    print("=" * 50)
    print(f"Collection complete!")
    print(f"  Days collected: {len(pending_dates)}")
    print(f"  Total fetched: {total_fetched}")
    print(f"  Total new: {total_new}")


if __name__ == "__main__":
    main()
