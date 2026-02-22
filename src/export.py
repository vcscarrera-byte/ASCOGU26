"""Export tweet data to CSV and JSONL."""

import csv
import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

TWEET_CSV_FIELDS = [
    "tweet_id", "author_id", "username", "name", "text", "created_at",
    "conversation_id", "lang", "source",
    "like_count", "retweet_count", "reply_count", "quote_count",
    "impression_count", "bookmark_count",
    "total_engagement", "is_curated",
]


def export_tweets_csv(conn: sqlite3.Connection, output_path: Path, date: str | None = None) -> int:
    """Export tweets to CSV. Returns row count."""
    query = """
        SELECT t.tweet_id, t.author_id, u.username, u.name, t.text, t.created_at,
               t.conversation_id, t.lang, t.source,
               t.like_count, t.retweet_count, t.reply_count, t.quote_count,
               t.impression_count, t.bookmark_count,
               (t.like_count + t.retweet_count + t.reply_count + t.quote_count) as total_engagement,
               u.is_curated
        FROM tweets t
        JOIN users u ON t.author_id = u.user_id
    """
    params: list = []
    if date:
        query += " WHERE DATE(t.created_at) = ?"
        params.append(date)
    query += " ORDER BY t.created_at DESC"

    rows = conn.execute(query, params).fetchall()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TWEET_CSV_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    logger.info(f"Exported {len(rows)} tweets to {output_path}")
    return len(rows)


def export_tweets_jsonl(conn: sqlite3.Connection, output_path: Path, date: str | None = None) -> int:
    """Export tweets to JSONL (one JSON object per line). Returns row count."""
    query = """
        SELECT t.*, u.name, u.username, u.profile_image_url, u.is_curated
        FROM tweets t
        JOIN users u ON t.author_id = u.user_id
    """
    params: list = []
    if date:
        query += " WHERE DATE(t.created_at) = ?"
        params.append(date)
    query += " ORDER BY t.created_at DESC"

    rows = conn.execute(query, params).fetchall()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")

    logger.info(f"Exported {len(rows)} tweets to {output_path}")
    return len(rows)
