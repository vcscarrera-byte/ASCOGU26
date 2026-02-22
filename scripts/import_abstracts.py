"""Import ASCO GU 2026 abstracts into the SQLite database.

Usage:
    python scripts/import_abstracts.py                          # Import from local JSON
    python scripts/import_abstracts.py --source path/to.json    # Custom source
    python scripts/import_abstracts.py --refetch                # Re-fetch from ASCO API
    python scripts/import_abstracts.py --relink                 # Re-run tweet-abstract linking only
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.abstract_classifier import classify_tumor_from_session, get_session_rank
from src.abstract_fetcher import abstracts_to_rows, extract_all_abstracts
from src.config import get_db_path
from src.db import create_tables, get_connection, upsert_abstracts_batch
from src.linker import link_tweets_to_abstracts

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DEFAULT_JSON = Path(__file__).resolve().parent.parent / "data" / "abstracts_raw.json"


def load_and_process_rows(source_path: Path) -> list[dict]:
    """Load raw JSON hits and convert to classified rows."""
    logger.info(f"Loading abstracts from {source_path}")
    with open(source_path, encoding="utf-8") as f:
        raw_hits = json.load(f)
    logger.info(f"Loaded {len(raw_hits)} raw hits")

    rows = abstracts_to_rows(raw_hits)

    # Classify each abstract
    for row in rows:
        row["tumor_type"] = classify_tumor_from_session(
            row.get("session_title", ""),
            row.get("title", ""),
            row.get("body", ""),
        )
        row["session_rank"] = get_session_rank(row.get("session_type", ""))

    # Stats
    tumor_counts: dict[str, int] = {}
    session_counts: dict[str, int] = {}
    for row in rows:
        t = row["tumor_type"] or "Unknown"
        s = row["session_type"] or "Unknown"
        tumor_counts[t] = tumor_counts.get(t, 0) + 1
        session_counts[s] = session_counts.get(s, 0) + 1

    logger.info("Classification results:")
    for t, c in sorted(tumor_counts.items(), key=lambda x: -x[1]):
        logger.info(f"  {c:4d} | {t}")
    logger.info("Session types:")
    for s, c in sorted(session_counts.items(), key=lambda x: -x[1]):
        logger.info(f"  {c:4d} | {s}")

    return rows


def main():
    parser = argparse.ArgumentParser(description="Import ASCO GU 2026 abstracts")
    parser.add_argument("--source", "-s", type=Path, default=None, help="Path to JSON file")
    parser.add_argument("--refetch", action="store_true", help="Re-fetch from ASCO API first")
    parser.add_argument("--relink", action="store_true", help="Only re-run tweet-abstract linking")
    args = parser.parse_args()

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    if args.relink:
        logger.info("Re-linking tweets to abstracts...")
        new_links = link_tweets_to_abstracts(conn)
        logger.info(f"Done. {new_links} new links created.")
        conn.close()
        return

    source = args.source or DEFAULT_JSON

    if args.refetch:
        logger.info("Re-fetching abstracts from ASCO API...")
        raw_hits = extract_all_abstracts()
        # Save fresh JSON
        source = DEFAULT_JSON
        source.parent.mkdir(parents=True, exist_ok=True)
        with open(source, "w", encoding="utf-8") as f:
            json.dump(raw_hits, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(raw_hits)} hits to {source}")

    if not source.exists():
        logger.error(f"Source file not found: {source}")
        logger.error("Run with --refetch to download from ASCO API, or provide --source path")
        sys.exit(1)

    rows = load_and_process_rows(source)

    # Filter out rows without abstract_number (Discussion entries etc.)
    valid_rows = [r for r in rows if r.get("abstract_number")]
    skipped = len(rows) - len(valid_rows)
    if skipped:
        logger.info(f"Skipping {skipped} entries without abstract_number")

    # Upsert into database
    total, new = upsert_abstracts_batch(conn, valid_rows)
    logger.info(f"Imported {total} abstracts ({new} new)")

    # Link tweets to abstracts
    new_links = link_tweets_to_abstracts(conn)
    logger.info(f"Tweet-abstract links: {new_links} new")

    conn.close()
    logger.info("Done!")


if __name__ == "__main__":
    main()
