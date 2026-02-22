"""Tests for topic modeling."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.topic_model import cluster_tweets, preprocess_tweet


def test_preprocess_removes_urls():
    text = "Check this out https://t.co/abc123 great data"
    result = preprocess_tweet(text)
    assert "https" not in result
    assert "great data" in result


def test_preprocess_removes_mentions():
    text = "@DrChoueiri presented amazing RCC data"
    result = preprocess_tweet(text)
    assert "@DrChoueiri" not in result
    assert "presented amazing rcc data" in result


def test_preprocess_normalizes_hashtags():
    text = "Data from #ASCOGU26 on #ProstateCancer"
    result = preprocess_tweet(text)
    assert "#" not in result
    assert "ascogu26" in result
    assert "prostatecancer" in result


def test_preprocess_removes_stop_words():
    text = "Great ASCO data on cancer treatment"
    result = preprocess_tweet(text, stop_words=["asco", "cancer", "treatment"])
    assert "asco" not in result
    assert "great" in result


def test_preprocess_removes_rt_prefix():
    text = "RT @someone Great prostate data"
    result = preprocess_tweet(text)
    assert not result.startswith("rt")


def test_cluster_too_few_tweets():
    tweets = [{"text": "Hello"}, {"text": "World"}]
    labels, topics, _ = cluster_tweets(tweets, n_clusters=3)
    # Should handle gracefully
    assert len(labels) == 2


def test_cluster_sufficient_tweets():
    tweets = [
        {"text": f"Pembrolizumab shows great efficacy in renal cell carcinoma trial {i}"}
        for i in range(20)
    ] + [
        {"text": f"Enzalutamide plus abiraterone for metastatic prostate cancer results {i}"}
        for i in range(20)
    ] + [
        {"text": f"Enfortumab vedotin bladder cancer urothelial treatment update {i}"}
        for i in range(20)
    ]

    labels, topics, processed = cluster_tweets(tweets, n_clusters=3)

    assert len(labels) == 60
    assert len(topics) == 3
    # Each topic should have top terms
    for tid, terms in topics.items():
        assert len(terms) > 0
