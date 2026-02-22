"""Tests for abstract_aggregator — query functions with filters."""

import sqlite3
import pytest
from src.db import create_tables, upsert_abstract
from src.abstract_aggregator import (
    get_all_abstracts,
    get_abstract_detail,
    get_abstract_stats,
    get_session_type_names,
)


@pytest.fixture
def conn():
    """In-memory DB with sample abstracts."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    create_tables(c)

    abstracts = [
        {
            "abstract_number": "100",
            "title": "Enzalutamide in mCRPC patients",
            "body": "Phase 3 trial of enzalutamide...",
            "presenter": "Dr. A",
            "session_type": "Oral Abstract Session",
            "session_title": "Oral Session A: Prostate Cancer",
            "drugs": "enzalutamide",
            "tumor_type": "Prostate",
            "session_rank": 5,
            "url": "https://asco.org/100",
        },
        {
            "abstract_number": "200",
            "title": "Pembrolizumab plus EV in bladder cancer",
            "body": "Combination of pembrolizumab and enfortumab vedotin...",
            "presenter": "Dr. B",
            "session_type": "Poster Session",
            "session_title": "Poster Session B: Urothelial Carcinoma",
            "drugs": "pembrolizumab; enfortumab vedotin",
            "tumor_type": "Bladder / Urothelial",
            "session_rank": 1,
            "url": "https://asco.org/200",
        },
        {
            "abstract_number": "300",
            "title": "Cabozantinib in RCC",
            "body": "Cabozantinib showed improved OS...",
            "presenter": "Dr. C",
            "session_type": "Rapid Oral Abstract Session",
            "session_title": "Rapid Oral Session C: Renal Cell Cancer",
            "drugs": "cabozantinib",
            "tumor_type": "Kidney / RCC",
            "session_rank": 4,
            "url": "https://asco.org/300",
        },
    ]
    for a in abstracts:
        upsert_abstract(c, a)
    c.commit()
    yield c
    c.close()


def test_get_all_abstracts_no_filter(conn):
    results = get_all_abstracts(conn, limit=100)
    assert len(results) == 3


def test_get_all_abstracts_filter_tumor(conn):
    results = get_all_abstracts(conn, selected_tumors=["Prostate"])
    assert len(results) == 1
    assert results[0]["abstract_number"] == "100"


def test_get_all_abstracts_filter_drug(conn):
    results = get_all_abstracts(conn, selected_drugs=["pembrolizumab"])
    assert len(results) == 1
    assert results[0]["abstract_number"] == "200"


def test_get_all_abstracts_filter_session(conn):
    results = get_all_abstracts(conn, session_types=["Oral Abstract Session"])
    assert len(results) == 1
    assert results[0]["abstract_number"] == "100"


def test_get_all_abstracts_text_search(conn):
    results = get_all_abstracts(conn, text_search="mCRPC")
    assert len(results) == 1
    assert results[0]["abstract_number"] == "100"


def test_get_all_abstracts_sort_session_rank(conn):
    results = get_all_abstracts(conn, sort_by="session_rank", limit=100)
    assert results[0]["abstract_number"] == "100"  # Oral = rank 5
    assert results[1]["abstract_number"] == "300"  # Rapid Oral = rank 4


def test_get_all_abstracts_empty_filter(conn):
    results = get_all_abstracts(conn, selected_tumors=["Testicular / Germ Cell"])
    assert len(results) == 0


def test_get_abstract_detail(conn):
    detail = get_abstract_detail(conn, "200")
    assert detail is not None
    assert detail["presenter"] == "Dr. B"
    assert detail["linked_tweet_count"] == 0


def test_get_abstract_detail_not_found(conn):
    assert get_abstract_detail(conn, "999") is None


def test_get_abstract_stats(conn):
    stats = get_abstract_stats(conn)
    assert stats["total"] == 3
    assert "Oral Abstract Session" in stats["by_session_type"]
    assert "Prostate" in stats["by_tumor"]
    assert "enzalutamide" in stats["top_drugs"]


def test_get_session_type_names(conn):
    names = get_session_type_names(conn)
    assert "Oral Abstract Session" in names
    assert "Poster Session" in names
    assert len(names) == 3
