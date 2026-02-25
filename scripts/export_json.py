#!/usr/bin/env python3
"""Export all SQLite data into static JSON files for the Next.js frontend.

Writes to frontend/public/data/*.json so the Next.js app can consume them
at build-time or as static assets.
"""

import json
import logging
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — allow importing from src/
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_db_path
from src.db import get_connection, create_tables, get_daily_brief, get_linked_tweets
from src.aggregator import (
    get_available_dates,
    get_quick_stats,
    get_top_tweets,
    get_all_tweets,
    get_top_authors,
    get_volume_by_day,
)
from src.abstract_aggregator import (
    get_all_abstracts,
    get_abstract_stats,
    get_abstracts_with_buzz,
    get_abstract_detail,
    get_session_type_names,
)
from src.clinical_filters import classify_tweet_text, get_tumor_type_names, get_drug_names
from src.relevance import rank_tweets_by_relevance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------
OUT_DIR = PROJECT_ROOT / "frontend" / "public" / "data"


def ensure_output_dir() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUT_DIR}")


def write_json(filename: str, data) -> None:
    """Write data to a JSON file with progress logging."""
    path = OUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    size_kb = path.stat().st_size / 1024
    logger.info(f"  -> {filename} ({size_kb:.1f} KB)")


def safe_query(label: str, func, *args, fallback=None, **kwargs):
    """Run a query function, returning a fallback on error (missing tables, etc.)."""
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        logger.warning(f"  [SKIP] {label}: {exc}")
        return fallback


def add_clinical_tags(tweets: list[dict]) -> list[dict]:
    """Add clinical_tags to each tweet dict using classify_tweet_text."""
    for t in tweets:
        t["clinical_tags"] = classify_tweet_text(t.get("text", ""))
    return tweets


# ---------------------------------------------------------------------------
# Export functions — one per JSON file
# ---------------------------------------------------------------------------

def export_stats(conn) -> None:
    print("Exporting stats.json ...")
    stats = safe_query("get_quick_stats", get_quick_stats, conn, fallback={})
    if stats is None:
        stats = {}
    # Add abstract count
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM abstracts").fetchone()
        stats["abstract_count"] = row["cnt"] if row else 0
    except Exception:
        stats["abstract_count"] = 0
    write_json("stats.json", stats)


def export_dates(conn) -> None:
    print("Exporting dates.json ...")
    dates = safe_query("get_available_dates", get_available_dates, conn, fallback=[])
    if dates is None:
        dates = []
    write_json("dates.json", dates)


def export_filters(conn) -> None:
    print("Exporting filters.json ...")
    tumor_types = safe_query("get_tumor_type_names", get_tumor_type_names, fallback=[])
    drug_names = safe_query("get_drug_names", get_drug_names, fallback=[])
    session_types = safe_query("get_session_type_names", get_session_type_names, conn, fallback=[])
    write_json("filters.json", {
        "tumor_types": tumor_types or [],
        "drug_names": drug_names or [],
        "session_types": session_types or [],
    })


def export_tweets_top(conn) -> None:
    print("Exporting tweets_top.json ...")
    tweets = safe_query("get_top_tweets", get_top_tweets, conn, limit=50, fallback=[])
    if tweets is None:
        tweets = []
    tweets = add_clinical_tags(tweets)
    tweets = rank_tweets_by_relevance(tweets)
    write_json("tweets_top.json", tweets)


def export_tweets_all(conn) -> None:
    print("Exporting tweets_all.json ...")
    tweets = safe_query("get_all_tweets", get_all_tweets, conn, limit=500, offset=0, fallback=[])
    if tweets is None:
        tweets = []
    tweets = add_clinical_tags(tweets)
    write_json("tweets_all.json", tweets)


def export_authors(conn) -> None:
    print("Exporting authors.json ...")
    authors = safe_query("get_top_authors", get_top_authors, conn, limit=50, fallback=[])
    if authors is None:
        authors = []
    write_json("authors.json", authors)


def export_abstracts_stats(conn) -> None:
    print("Exporting abstracts_stats.json ...")
    stats = safe_query("get_abstract_stats", get_abstract_stats, conn, fallback={})
    if stats is None:
        stats = {}
    write_json("abstracts_stats.json", stats)


def export_abstracts_buzz(conn) -> None:
    print("Exporting abstracts_buzz.json ...")
    abstracts = safe_query("get_abstracts_with_buzz", get_abstracts_with_buzz, conn, limit=10, fallback=[])
    if abstracts is None:
        abstracts = []
    write_json("abstracts_buzz.json", abstracts)


def export_abstracts_all(conn) -> None:
    print("Exporting abstracts_all.json ...")
    abstracts = safe_query("get_all_abstracts", get_all_abstracts, conn, limit=200, fallback=[])
    if abstracts is None:
        abstracts = []
    write_json("abstracts_all.json", abstracts)


def export_abstracts_detail(conn) -> None:
    print("Exporting abstracts_detail.json ...")
    # Fetch all abstract numbers first
    try:
        rows = conn.execute("SELECT abstract_number FROM abstracts ORDER BY abstract_number").fetchall()
        abstract_numbers = [r["abstract_number"] for r in rows]
    except Exception as exc:
        logger.warning(f"  [SKIP] abstracts_detail: {exc}")
        write_json("abstracts_detail.json", {})
        return

    detail_map: dict[str, dict] = {}
    for i, num in enumerate(abstract_numbers):
        detail = get_abstract_detail(conn, num)
        if detail:
            linked = safe_query(
                f"get_linked_tweets({num})", get_linked_tweets, conn, num, fallback=[],
            )
            detail["linked_tweets"] = linked or []
            detail_map[num] = detail
        if (i + 1) % 100 == 0:
            logger.info(f"    ... processed {i + 1}/{len(abstract_numbers)} abstracts")

    write_json("abstracts_detail.json", detail_map)


def export_drug_mentions(conn) -> None:
    """Count drug mentions across all tweets using clinical_filters."""
    print("Exporting drug_mentions.json ...")
    try:
        rows = conn.execute("SELECT text FROM tweets").fetchall()
        from collections import Counter
        drug_counter: Counter[str] = Counter()
        for row in rows:
            tags = classify_tweet_text(row["text"])
            for drug in tags.get("drugs", []):
                drug_counter[drug] += 1
        # Return sorted list of {drug, count}
        mentions = [{"drug": d, "count": c} for d, c in drug_counter.most_common(20)]
        write_json("drug_mentions.json", mentions)
    except Exception as exc:
        logger.warning(f"  [SKIP] drug_mentions: {exc}")
        write_json("drug_mentions.json", [])


def export_metrics_volume(conn) -> None:
    print("Exporting metrics_volume.json ...")
    volume = safe_query("get_volume_by_day", get_volume_by_day, conn, fallback=[])
    if volume is None:
        volume = []
    write_json("metrics_volume.json", volume)


def export_briefs(conn) -> None:
    print("Exporting briefs.json ...")
    dates = safe_query("get_available_dates", get_available_dates, conn, fallback=[])
    if not dates:
        write_json("briefs.json", {})
        return

    briefs: dict[str, dict] = {}
    for date in dates:
        brief_pt = safe_query(f"brief_pt({date})", get_daily_brief, conn, date, "pt", fallback=None)
        brief_en = safe_query(f"brief_en({date})", get_daily_brief, conn, date, "en", fallback=None)
        if brief_pt or brief_en:
            briefs[date] = {
                "pt": brief_pt,
                "en": brief_en,
            }
    write_json("briefs.json", briefs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    start = time.time()
    print("=" * 60)
    print("ASCO GU 2026 — Static JSON Export")
    print("=" * 60)

    ensure_output_dir()

    db_path = get_db_path()
    logger.info(f"Database: {db_path}")
    conn = get_connection(db_path)
    create_tables(conn)

    export_stats(conn)
    export_dates(conn)
    export_filters(conn)
    export_tweets_top(conn)
    export_tweets_all(conn)
    export_authors(conn)
    export_abstracts_stats(conn)
    export_abstracts_buzz(conn)
    export_abstracts_all(conn)
    export_abstracts_detail(conn)
    export_drug_mentions(conn)
    export_metrics_volume(conn)
    export_briefs(conn)

    conn.close()

    elapsed = time.time() - start
    print("=" * 60)
    print(f"Done! {elapsed:.1f}s elapsed. Files written to {OUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
