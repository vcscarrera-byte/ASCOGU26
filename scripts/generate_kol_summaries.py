#!/usr/bin/env python3
"""Generate per-KOL daily summaries using Claude API."""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_db_path
from src.db import get_connection, create_tables
from src.kol_summarizer import generate_all_kol_summaries

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    import argparse

    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    parser = argparse.ArgumentParser(description="Generate KOL summaries")
    parser.add_argument("--date", default=yesterday, help="Date (YYYY-MM-DD)")
    parser.add_argument("--min-tweets", type=int, default=2, help="Min tweets to qualify")
    args = parser.parse_args()

    print("=" * 60)
    print(f"ASCO GU 2026 — KOL Summaries for {args.date}")
    print("=" * 60)

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    stats = generate_all_kol_summaries(conn, args.date, min_tweets=args.min_tweets)
    conn.close()

    print(f"\nResults: {stats['kols_found']} KOLs found, {stats['summaries_generated']} summaries generated")


if __name__ == "__main__":
    main()
