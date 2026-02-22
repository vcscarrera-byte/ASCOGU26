"""Shared test fixtures."""

import sqlite3

import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.db import create_tables


@pytest.fixture
def db_conn():
    """In-memory SQLite database with schema created."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    create_tables(conn)
    yield conn
    conn.close()


@pytest.fixture
def sample_tweet():
    """A sample tweet dict matching X API v2 response shape."""
    return {
        "id": "1234567890123456789",
        "author_id": "9876543210",
        "text": "Exciting data on pembrolizumab + lenvatinib in renal cell carcinoma at #ASCOGU26! OS benefit confirmed.",
        "created_at": "2026-02-26T14:30:00.000Z",
        "conversation_id": "1234567890123456789",
        "in_reply_to_user_id": None,
        "lang": "en",
        "source": "Twitter Web App",
        "public_metrics": {
            "retweet_count": 45,
            "reply_count": 12,
            "like_count": 230,
            "quote_count": 8,
            "impression_count": 15000,
            "bookmark_count": 35,
        },
        "referenced_tweets": None,
        "entities": {
            "hashtags": [{"tag": "ASCOGU26"}],
        },
        "context_annotations": None,
    }


@pytest.fixture
def sample_user():
    """A sample user dict matching X API v2 response shape."""
    return {
        "id": "9876543210",
        "name": "Dr. Test Oncologist",
        "username": "DrTestOnc",
        "description": "GU Oncologist at Test Cancer Center",
        "profile_image_url": "https://pbs.twimg.com/profile_images/test.jpg",
        "verified": True,
        "public_metrics": {
            "followers_count": 5000,
            "following_count": 300,
            "tweet_count": 2500,
            "listed_count": 150,
        },
    }


@pytest.fixture
def sample_api_response(sample_tweet, sample_user):
    """A sample X API v2 search/recent response."""
    return {
        "data": [sample_tweet],
        "includes": {
            "users": [sample_user],
        },
        "meta": {
            "newest_id": "1234567890123456789",
            "oldest_id": "1234567890123456789",
            "result_count": 1,
        },
    }
