"""Tests for aggregation routines."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.aggregator import compute_daily_metrics, get_top_authors, get_top_tweets, get_volume_by_day
from src.db import create_collection_run, insert_tweet, upsert_user


def _seed_data(db_conn):
    """Seed the database with test tweets."""
    users = [
        {"id": "100", "username": "doctor_a", "name": "Doctor A",
         "public_metrics": {"followers_count": 5000, "following_count": 100, "tweet_count": 500, "listed_count": 10}},
        {"id": "200", "username": "doctor_b", "name": "Doctor B",
         "public_metrics": {"followers_count": 3000, "following_count": 200, "tweet_count": 300, "listed_count": 5}},
    ]
    for u in users:
        upsert_user(db_conn, u)

    run_id = create_collection_run(db_conn, "test", "2026-02-26T00:00:00Z", "2026-02-27T00:00:00Z")

    tweets = [
        {"id": "1", "author_id": "100", "text": "Great prostate data #ASCOGU26",
         "created_at": "2026-02-26T10:00:00Z", "conversation_id": "1",
         "public_metrics": {"retweet_count": 10, "reply_count": 5, "like_count": 50, "quote_count": 3,
                            "impression_count": 1000, "bookmark_count": 5}},
        {"id": "2", "author_id": "100", "text": "Follow-up on the prostate trial",
         "created_at": "2026-02-26T11:00:00Z", "conversation_id": "1",
         "public_metrics": {"retweet_count": 5, "reply_count": 2, "like_count": 20, "quote_count": 1,
                            "impression_count": 500, "bookmark_count": 2}},
        {"id": "3", "author_id": "200", "text": "Bladder cancer breakthrough #ASCOGU26",
         "created_at": "2026-02-26T12:00:00Z", "conversation_id": "3",
         "public_metrics": {"retweet_count": 100, "reply_count": 30, "like_count": 500, "quote_count": 20,
                            "impression_count": 50000, "bookmark_count": 100}},
        {"id": "4", "author_id": "200", "text": "Day 2 highlights",
         "created_at": "2026-02-27T09:00:00Z", "conversation_id": "4",
         "public_metrics": {"retweet_count": 8, "reply_count": 3, "like_count": 40, "quote_count": 2,
                            "impression_count": 2000, "bookmark_count": 8}},
    ]
    for t in tweets:
        insert_tweet(db_conn, t, run_id)
    db_conn.commit()

    return run_id


def test_compute_daily_metrics(db_conn):
    _seed_data(db_conn)
    summary = compute_daily_metrics(db_conn, "2026-02-26")

    assert summary["total_tweets"] == 3  # 3 tweets on Feb 26
    assert summary["unique_authors"] == 2
    # Engagement: (10+5+50+3) + (5+2+20+1) + (100+30+500+20) = 68 + 28 + 650 = 746
    assert summary["total_engagement"] == 746


def test_get_top_tweets(db_conn):
    _seed_data(db_conn)
    top = get_top_tweets(db_conn, date="2026-02-26", limit=5)

    assert len(top) == 3
    # First should be the bladder cancer tweet (highest engagement)
    assert top[0]["tweet_id"] == "3"
    assert top[0]["total_engagement"] == 650


def test_get_top_authors(db_conn):
    _seed_data(db_conn)
    authors = get_top_authors(db_conn, date="2026-02-26")

    assert len(authors) == 2
    # Doctor B should be first (higher engagement)
    assert authors[0]["username"] == "doctor_b"


def test_get_volume_by_day(db_conn):
    _seed_data(db_conn)
    volume = get_volume_by_day(db_conn)

    assert len(volume) == 2  # Feb 26 and Feb 27
    feb26 = next(v for v in volume if v["date"] == "2026-02-26")
    assert feb26["tweets"] == 3
    assert feb26["authors"] == 2


def test_empty_date(db_conn):
    _seed_data(db_conn)
    summary = compute_daily_metrics(db_conn, "2026-03-01")
    assert summary["total_tweets"] == 0


def test_get_top_tweets_filtered_by_tumor(db_conn):
    """Filter tweets by tumor type 'Prostate'."""
    _seed_data(db_conn)
    top = get_top_tweets(db_conn, selected_tumors=["Prostate"])

    # Only tweets 1 and 2 mention prostate
    assert len(top) == 2
    for t in top:
        assert "prostate" in t["text"].lower()


def test_get_top_tweets_filtered_by_tumor_bladder(db_conn):
    """Filter tweets by tumor type 'Bladder / Urothelial'."""
    _seed_data(db_conn)
    top = get_top_tweets(db_conn, selected_tumors=["Bladder / Urothelial"])

    # Only tweet 3 mentions bladder
    assert len(top) == 1
    assert top[0]["tweet_id"] == "3"


def test_get_top_tweets_no_match_filter(db_conn):
    """Filter by drug that doesn't exist in data."""
    _seed_data(db_conn)
    top = get_top_tweets(db_conn, selected_drugs=["tivozanib"])

    assert len(top) == 0


def test_get_volume_by_day_filtered(db_conn):
    """Volume filtered by tumor type."""
    _seed_data(db_conn)
    volume = get_volume_by_day(db_conn, selected_tumors=["Prostate"])

    # Only Feb 26 should have prostate tweets
    assert len(volume) == 1
    assert volume[0]["date"] == "2026-02-26"
    assert volume[0]["tweets"] == 2


def test_get_top_authors_filtered(db_conn):
    """Authors filtered by tumor type."""
    _seed_data(db_conn)
    authors = get_top_authors(db_conn, selected_tumors=["Bladder / Urothelial"])

    # Only doctor_b has bladder tweets
    assert len(authors) == 1
    assert authors[0]["username"] == "doctor_b"
