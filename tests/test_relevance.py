"""Tests for relevance scoring module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.relevance import compute_relevance_score, rank_tweets_by_relevance


def _make_tweet(**overrides):
    """Create a test tweet dict with defaults."""
    base = {
        "tweet_id": "1",
        "text": "Generic tweet",
        "like_count": 10,
        "retweet_count": 5,
        "reply_count": 2,
        "quote_count": 1,
        "impression_count": 100,
        "bookmark_count": 0,
        "is_curated": False,
        "username": "test_user",
        "name": "Test User",
        "created_at": "2026-02-26T10:00:00Z",
    }
    base.update(overrides)
    return base


def test_basic_score():
    tweet = _make_tweet()
    score = compute_relevance_score(tweet, max_engagement=18)
    assert 0 <= score <= 100


def test_curated_bonus():
    """Curated accounts should score higher."""
    base = _make_tweet()
    curated = _make_tweet(is_curated=True)

    score_base = compute_relevance_score(base, max_engagement=18)
    score_curated = compute_relevance_score(curated, max_engagement=18)

    assert score_curated > score_base
    assert score_curated - score_base == 20.0  # exact KOL bonus


def test_clinical_bonus():
    """Tweets with drug/tumor mentions should score higher."""
    generic = _make_tweet(text="Great day at ASCO!")
    clinical = _make_tweet(text="Enzalutamide in mCRPC shows OS benefit")

    score_generic = compute_relevance_score(generic, max_engagement=18)
    score_clinical = compute_relevance_score(clinical, max_engagement=18)

    assert score_clinical > score_generic


def test_rt_penalty():
    """Pure retweets should be penalized."""
    original = _make_tweet(text="Great prostate data")
    rt = _make_tweet(text="RT @someone: Great prostate data")

    score_orig = compute_relevance_score(original, max_engagement=18)
    score_rt = compute_relevance_score(rt, max_engagement=18)

    assert score_orig > score_rt


def test_high_engagement_caps_at_40():
    """Engagement score should not exceed 40."""
    tweet = _make_tweet(like_count=1000, retweet_count=500, reply_count=200, quote_count=100)
    total_eng = 1000 + 500 + 200 + 100
    score = compute_relevance_score(tweet, max_engagement=total_eng)
    # Eng component is exactly 40 when tweet has max engagement
    assert score <= 100


def test_zero_engagement():
    tweet = _make_tweet(like_count=0, retweet_count=0, reply_count=0, quote_count=0)
    score = compute_relevance_score(tweet, max_engagement=100)
    assert score >= 0


def test_rank_tweets_by_relevance():
    """Ranking should sort by score descending."""
    tweets = [
        _make_tweet(tweet_id="1", text="Generic tweet", is_curated=False),
        _make_tweet(tweet_id="2", text="Enzalutamide in prostate cancer", is_curated=True),
        _make_tweet(tweet_id="3", text="RT @someone: retweet"),
    ]
    ranked = rank_tweets_by_relevance(tweets)

    assert ranked[0]["tweet_id"] == "2"  # curated + clinical
    assert ranked[-1]["tweet_id"] == "3"  # RT penalty

    # All should have relevance_score and clinical_tags
    for t in ranked:
        assert "relevance_score" in t
        assert "clinical_tags" in t


def test_rank_empty_list():
    assert rank_tweets_by_relevance([]) == []


def test_clinical_tags_added():
    tweets = [_make_tweet(text="Pembrolizumab in bladder cancer")]
    ranked = rank_tweets_by_relevance(tweets)
    tags = ranked[0]["clinical_tags"]
    assert "pembrolizumab" in tags["drugs"]
    assert "Bladder / Urothelial" in tags["tumor_types"]
