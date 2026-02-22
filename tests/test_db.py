"""Tests for database operations."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import (
    create_collection_run,
    finish_collection_run,
    insert_tweet,
    upsert_user,
)


def test_create_tables(db_conn):
    """Tables should exist after creation."""
    tables = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = {t["name"] for t in tables}
    assert "collection_runs" in table_names
    assert "users" in table_names
    assert "tweets" in table_names
    assert "daily_metrics" in table_names
    assert "daily_briefs" in table_names


def test_insert_tweet_dedup(db_conn, sample_tweet, sample_user):
    """Inserting the same tweet twice should not create duplicates."""
    # Insert user first (FK)
    upsert_user(db_conn, sample_user)
    db_conn.commit()

    run_id = create_collection_run(db_conn, "test", "2026-02-26T00:00:00Z", "2026-02-27T00:00:00Z")

    # First insert should succeed
    result1 = insert_tweet(db_conn, sample_tweet, run_id)
    db_conn.commit()

    # Second insert of same tweet should be ignored
    result2 = insert_tweet(db_conn, sample_tweet, run_id)
    db_conn.commit()

    # Count should be 1
    row = db_conn.execute("SELECT COUNT(*) as cnt FROM tweets").fetchone()
    assert row["cnt"] == 1


def test_upsert_user_updates(db_conn, sample_user):
    """Upserting a user should update fields."""
    upsert_user(db_conn, sample_user)
    db_conn.commit()

    # Update name
    updated = dict(sample_user)
    updated["name"] = "Dr. Updated Name"
    upsert_user(db_conn, updated)
    db_conn.commit()

    row = db_conn.execute("SELECT name FROM users WHERE user_id=?", (sample_user["id"],)).fetchone()
    assert row["name"] == "Dr. Updated Name"


def test_upsert_user_curated_flag(db_conn, sample_user):
    """Curated flag should be set when username matches."""
    curated = {sample_user["username"].lower()}
    upsert_user(db_conn, sample_user, curated_usernames=curated)
    db_conn.commit()

    row = db_conn.execute("SELECT is_curated FROM users WHERE user_id=?", (sample_user["id"],)).fetchone()
    assert row["is_curated"] == 1


def test_collection_run_lifecycle(db_conn):
    """Test creating and finishing a collection run."""
    run_id = create_collection_run(db_conn, "hash123", "2026-02-26T00:00:00Z", "2026-02-27T00:00:00Z")
    assert run_id is not None

    row = db_conn.execute("SELECT status FROM collection_runs WHERE id=?", (run_id,)).fetchone()
    assert row["status"] == "running"

    finish_collection_run(db_conn, run_id, 100, 95, "completed")

    row = db_conn.execute("SELECT * FROM collection_runs WHERE id=?", (run_id,)).fetchone()
    assert row["status"] == "completed"
    assert row["tweets_fetched"] == 100
    assert row["tweets_new"] == 95
    assert row["finished_at"] is not None


def test_tweet_public_metrics_stored(db_conn, sample_tweet, sample_user):
    """Public metrics should be stored as individual columns."""
    upsert_user(db_conn, sample_user)
    db_conn.commit()
    run_id = create_collection_run(db_conn, "test", "2026-02-26T00:00:00Z", "2026-02-27T00:00:00Z")

    insert_tweet(db_conn, sample_tweet, run_id)
    db_conn.commit()

    row = db_conn.execute("SELECT * FROM tweets WHERE tweet_id=?", (sample_tweet["id"],)).fetchone()
    assert row["like_count"] == 230
    assert row["retweet_count"] == 45
    assert row["reply_count"] == 12
    assert row["quote_count"] == 8
