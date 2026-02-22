"""Compute daily aggregate metrics from collected tweets."""

import logging
import sqlite3
from datetime import datetime, timezone

from src.clinical_filters import build_text_filter_clause

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _upsert_metric(
    conn: sqlite3.Connection,
    date: str,
    metric_name: str,
    metric_value: float,
    breakdown_key: str = "",
    breakdown_value: str = "",
) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO daily_metrics
           (date, metric_name, metric_value, breakdown_key, breakdown_value, computed_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (date, metric_name, metric_value, breakdown_key, breakdown_value, _now_iso()),
    )


def _build_where(
    conditions: list[str],
    params: list,
    date: str | None = None,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
    date_column: str = "t.created_at",
    text_column: str = "t.text",
) -> None:
    """Append date and clinical filter conditions in-place."""
    if date:
        conditions.append(f"DATE({date_column}) = ?")
        params.append(date)
    filter_clause, filter_params = build_text_filter_clause(
        selected_tumors, selected_drugs, text_column=text_column,
    )
    if filter_clause:
        conditions.append(filter_clause)
        params.extend(filter_params)


def compute_daily_metrics(conn: sqlite3.Connection, date: str) -> dict:
    """Compute and store all daily metrics for a given date.

    Returns a summary dict.
    """
    logger.info(f"Computing metrics for {date}")

    # Total tweets
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM tweets WHERE DATE(created_at) = ?", (date,)
    ).fetchone()
    total_tweets = row["cnt"]
    _upsert_metric(conn, date, "total_tweets", total_tweets)

    # Total engagement
    row = conn.execute(
        """SELECT COALESCE(SUM(like_count + retweet_count + reply_count + quote_count), 0) as eng
           FROM tweets WHERE DATE(created_at) = ?""",
        (date,),
    ).fetchone()
    total_engagement = row["eng"]
    _upsert_metric(conn, date, "total_engagement", total_engagement)

    # Unique authors
    row = conn.execute(
        "SELECT COUNT(DISTINCT author_id) as cnt FROM tweets WHERE DATE(created_at) = ?",
        (date,),
    ).fetchone()
    unique_authors = row["cnt"]
    _upsert_metric(conn, date, "unique_authors", unique_authors)

    # Total likes, retweets, replies, quotes
    for metric in ["like_count", "retweet_count", "reply_count", "quote_count"]:
        row = conn.execute(
            f"SELECT COALESCE(SUM({metric}), 0) as val FROM tweets WHERE DATE(created_at) = ?",
            (date,),
        ).fetchone()
        _upsert_metric(conn, date, f"total_{metric}", row["val"])

    # Top 20 tweets by engagement (store as breakdown)
    rows = conn.execute(
        """SELECT t.tweet_id,
                  (t.like_count + t.retweet_count + t.reply_count + t.quote_count) as eng
           FROM tweets t
           WHERE DATE(t.created_at) = ?
           ORDER BY eng DESC
           LIMIT 20""",
        (date,),
    ).fetchall()
    for rank, row in enumerate(rows, 1):
        _upsert_metric(conn, date, "top_tweet_engagement", row["eng"],
                        "rank", str(rank))
        _upsert_metric(conn, date, "top_tweet_id", 0,
                        f"rank_{rank}", row["tweet_id"])

    # Top authors by engagement
    rows = conn.execute(
        """SELECT t.author_id, u.username,
                  COUNT(t.tweet_id) as tweet_cnt,
                  SUM(t.like_count + t.retweet_count + t.reply_count + t.quote_count) as eng
           FROM tweets t
           JOIN users u ON t.author_id = u.user_id
           WHERE DATE(t.created_at) = ?
           GROUP BY t.author_id
           ORDER BY eng DESC
           LIMIT 20""",
        (date,),
    ).fetchall()
    for rank, row in enumerate(rows, 1):
        _upsert_metric(conn, date, "top_author_engagement", row["eng"],
                        f"rank_{rank}", row["username"])

    # Top threads by conversation_id
    rows = conn.execute(
        """SELECT conversation_id, COUNT(*) as thread_size,
                  SUM(like_count + retweet_count + reply_count + quote_count) as eng
           FROM tweets
           WHERE DATE(created_at) = ? AND conversation_id IS NOT NULL
           GROUP BY conversation_id
           HAVING thread_size > 1
           ORDER BY eng DESC
           LIMIT 20""",
        (date,),
    ).fetchall()
    for rank, row in enumerate(rows, 1):
        _upsert_metric(conn, date, "top_thread_engagement", row["eng"],
                        f"rank_{rank}", row["conversation_id"])
        _upsert_metric(conn, date, "top_thread_size", row["thread_size"],
                        f"rank_{rank}", row["conversation_id"])

    conn.commit()

    summary = {
        "date": date,
        "total_tweets": total_tweets,
        "total_engagement": total_engagement,
        "unique_authors": unique_authors,
    }
    logger.info(f"Metrics computed: {summary}")
    return summary


def get_top_tweets(
    conn: sqlite3.Connection,
    date: str | None = None,
    limit: int = 20,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
) -> list[dict]:
    """Get top tweets by engagement, optionally filtered by date and clinical terms."""
    query = """
        SELECT t.tweet_id, t.text, t.created_at, t.author_id,
               t.like_count, t.retweet_count, t.reply_count, t.quote_count,
               t.impression_count, t.conversation_id,
               (t.like_count + t.retweet_count + t.reply_count + t.quote_count) as total_engagement,
               u.name, u.username, u.profile_image_url, u.is_curated,
               u.description as user_bio, u.verified, u.followers_count
        FROM tweets t
        JOIN users u ON t.author_id = u.user_id
    """
    conditions: list[str] = []
    params: list = []
    _build_where(conditions, params, date, selected_tumors, selected_drugs)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY total_engagement DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_top_authors(
    conn: sqlite3.Connection,
    date: str | None = None,
    limit: int = 20,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
) -> list[dict]:
    """Get top authors by total engagement."""
    query = """
        SELECT u.user_id, u.name, u.username, u.profile_image_url, u.is_curated,
               u.followers_count,
               COUNT(t.tweet_id) as tweet_count,
               SUM(t.like_count + t.retweet_count + t.reply_count + t.quote_count) as total_engagement,
               AVG(t.like_count + t.retweet_count + t.reply_count + t.quote_count) as avg_engagement
        FROM tweets t
        JOIN users u ON t.author_id = u.user_id
    """
    conditions: list[str] = []
    params: list = []
    _build_where(conditions, params, date, selected_tumors, selected_drugs)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " GROUP BY u.user_id ORDER BY total_engagement DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_top_threads(
    conn: sqlite3.Connection,
    date: str | None = None,
    limit: int = 20,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
) -> list[dict]:
    """Get top threads by engagement."""
    query = """
        SELECT conversation_id,
               COUNT(*) as thread_size,
               MIN(created_at) as started_at,
               SUM(like_count + retweet_count + reply_count + quote_count) as total_engagement
        FROM tweets t
        WHERE conversation_id IS NOT NULL
    """
    conditions: list[str] = []
    params: list = []
    _build_where(
        conditions, params, date, selected_tumors, selected_drugs,
        date_column="t.created_at", text_column="t.text",
    )

    for cond in conditions:
        query += f" AND {cond}"
    query += " GROUP BY conversation_id HAVING thread_size > 1 ORDER BY total_engagement DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_thread_tweets(conn: sqlite3.Connection, conversation_id: str) -> list[dict]:
    """Get all tweets in a thread."""
    rows = conn.execute(
        """SELECT t.*, u.name, u.username, u.profile_image_url
           FROM tweets t JOIN users u ON t.author_id = u.user_id
           WHERE t.conversation_id = ?
           ORDER BY t.created_at ASC""",
        (conversation_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_volume_by_day(
    conn: sqlite3.Connection,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
) -> list[dict]:
    """Get tweet count and engagement per day, optionally filtered."""
    query = """
        SELECT DATE(t.created_at) as date,
               COUNT(*) as tweets,
               COUNT(DISTINCT t.author_id) as authors,
               SUM(t.like_count) as likes,
               SUM(t.retweet_count) as retweets,
               SUM(t.reply_count) as replies,
               SUM(t.quote_count) as quotes,
               SUM(t.like_count + t.retweet_count + t.reply_count + t.quote_count) as engagement
        FROM tweets t
    """
    conditions: list[str] = []
    params: list = []
    filter_clause, filter_params = build_text_filter_clause(
        selected_tumors, selected_drugs, text_column="t.text",
    )
    if filter_clause:
        conditions.append(filter_clause)
        params.extend(filter_params)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " GROUP BY DATE(t.created_at) ORDER BY date"

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_all_tweets(
    conn: sqlite3.Connection,
    date: str | None = None,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
    text_search: str | None = None,
    limit: int = 200,
) -> list[dict]:
    """Get all tweets with full user info, filtered and limited.

    Used by the Feed page for browsing all tweets.
    """
    query = """
        SELECT t.tweet_id, t.text, t.created_at, t.author_id,
               t.like_count, t.retweet_count, t.reply_count, t.quote_count,
               t.impression_count, t.bookmark_count, t.conversation_id,
               t.referenced_tweets, t.entities,
               (t.like_count + t.retweet_count + t.reply_count + t.quote_count) as total_engagement,
               u.name, u.username, u.profile_image_url, u.is_curated,
               u.followers_count, u.description as user_bio
        FROM tweets t
        JOIN users u ON t.author_id = u.user_id
    """
    conditions: list[str] = []
    params: list = []
    _build_where(conditions, params, date, selected_tumors, selected_drugs)

    if text_search and text_search.strip():
        conditions.append("LOWER(t.text) LIKE ?")
        params.append(f"%{text_search.strip().lower()}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY t.created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_quick_stats(
    conn: sqlite3.Connection,
    date: str | None = None,
) -> dict:
    """Get quick summary stats for a date (or all dates)."""
    if date:
        where = "WHERE DATE(created_at) = ?"
        params = [date]
    else:
        where = ""
        params = []

    row = conn.execute(
        f"SELECT COUNT(*) as total_tweets, COUNT(DISTINCT author_id) as unique_authors,"
        f" COALESCE(SUM(like_count + retweet_count + reply_count + quote_count), 0) as total_engagement"
        f" FROM tweets {where}",
        params,
    ).fetchone()

    curated_params = list(params)
    curated_where = f"{where} {'AND' if where else 'WHERE'} author_id IN (SELECT user_id FROM users WHERE is_curated = 1)"
    curated_row = conn.execute(
        f"SELECT COUNT(DISTINCT author_id) as cnt FROM tweets {curated_where}",
        curated_params,
    ).fetchone()

    return {
        "total_tweets": row["total_tweets"],
        "unique_authors": row["unique_authors"],
        "total_engagement": row["total_engagement"],
        "curated_active": curated_row["cnt"],
    }


def get_available_dates(conn: sqlite3.Connection) -> list[str]:
    """Get all dates that have collected tweets."""
    rows = conn.execute(
        "SELECT DISTINCT DATE(created_at) as date FROM tweets ORDER BY date"
    ).fetchall()
    return [r["date"] for r in rows]
