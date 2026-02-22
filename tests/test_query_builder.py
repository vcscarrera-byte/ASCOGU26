"""Tests for query builder."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.query_builder import build_account_queries, build_all_queries, build_hashtag_query


def test_hashtag_query_basic():
    q = build_hashtag_query(["#ASCOGU26"])
    assert q == "#ASCOGU26"


def test_hashtag_query_multiple():
    q = build_hashtag_query(["#ASCOGU26", "#ASCOGU2026", "#ASCOGU"])
    assert q == "#ASCOGU26 OR #ASCOGU2026 OR #ASCOGU"


def test_hashtag_query_with_keywords():
    q = build_hashtag_query(["#ASCOGU26"], ["ASCO GU 2026"])
    assert q == '#ASCOGU26 OR "ASCO GU 2026"'


def test_account_queries_fit_within_limit():
    accounts = [f"user{i}" for i in range(30)]
    filters = ["prostate", "bladder", "kidney", "GU", "ASCO"]
    queries = build_account_queries(accounts, filters, max_length=512)

    for q in queries:
        assert len(q) <= 512, f"Query too long ({len(q)} chars): {q[:80]}..."

    # All accounts should appear across all queries
    all_accounts_in_queries = set()
    for q in queries:
        for acc in accounts:
            if f"from:{acc}" in q:
                all_accounts_in_queries.add(acc)
    assert all_accounts_in_queries == set(accounts)


def test_account_queries_empty():
    assert build_account_queries([], ["GU"]) == []


def test_account_queries_single():
    queries = build_account_queries(["testuser"], ["GU", "ASCO"])
    assert len(queries) == 1
    assert "from:testuser" in queries[0]
    assert "GU" in queries[0]


def test_build_all_queries():
    queries = build_all_queries(
        hashtags=["#ASCOGU26", "#ASCOGU"],
        keywords=["ASCO GU 2026"],
        accounts=[f"user{i}" for i in range(30)],
        account_filters=["prostate", "bladder", "kidney", "renal", "urothelial", "GU", "ASCO"],
        max_length=512,
    )
    # Should have 1 hashtag query + N account batch queries
    assert len(queries) >= 2

    # First query should be the hashtag query
    assert "#ASCOGU26" in queries[0]

    # All queries within limit
    for q in queries:
        assert len(q) <= 512


def test_build_all_queries_with_real_config():
    """Test with the actual config values from config.yaml."""
    accounts = [
        "DrChoueiri", "DrRanaMcKay", "PGrivasMDPhD", "OJSartor",
        "neerajaiims", "TiansterZhang", "MattGalsky", "BradMcG04",
        "sonpavde", "cnsternberg", "CaPsurvivorship", "UroDocAsh",
        "LoebStacy", "zklaassen_md", "daniel_j_george", "Beam_Doc",
        "williamohmd", "amerseburger", "elizabethdkatz", "TomPowlesMD",
        "monaborea", "MTBourlon", "KarimFizazi", "AndreaNecchi",
        "ASCO", "urotoday", "OncLive", "OncoAlert", "ASCOPost", "GUOncologyNow",
    ]
    queries = build_all_queries(
        hashtags=["#ASCOGU26", "#ASCOGU2026", "#ASCOGU"],
        keywords=["ASCO GU 2026"],
        accounts=accounts,
        account_filters=["prostate", "bladder", "kidney", "renal", "urothelial", "GU", "ASCO"],
        max_length=512,
    )
    for i, q in enumerate(queries):
        print(f"Query {i} ({len(q)} chars): {q[:100]}...")
        assert len(q) <= 512, f"Query {i} is {len(q)} chars"
