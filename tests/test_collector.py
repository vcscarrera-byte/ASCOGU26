"""Tests for collector (mocked API calls)."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import responses

from src.collector import XApiClient


@responses.activate
def test_search_recent_basic(sample_api_response):
    """Test basic search_recent call with mocked API."""
    responses.add(
        responses.GET,
        "https://api.x.com/2/tweets/search/recent",
        json=sample_api_response,
        status=200,
        headers={
            "x-rate-limit-remaining": "449",
            "x-rate-limit-reset": "9999999999",
        },
    )

    client = XApiClient(bearer_token="test_token")
    result = client.search_recent(
        query="#ASCOGU26",
        start_time="2026-02-26T00:00:00Z",
        end_time="2026-02-27T00:00:00Z",
    )

    assert "data" in result
    assert len(result["data"]) == 1
    assert result["data"][0]["id"] == "1234567890123456789"


@responses.activate
def test_search_all_pages_pagination(sample_tweet, sample_user):
    """Test pagination with next_token."""
    # Page 1: has next_token
    page1 = {
        "data": [sample_tweet],
        "includes": {"users": [sample_user]},
        "meta": {"result_count": 1, "next_token": "abc123"},
    }
    # Page 2: no next_token (last page)
    tweet2 = dict(sample_tweet)
    tweet2["id"] = "9999999999999999999"
    tweet2["text"] = "Another tweet about kidney cancer"
    page2 = {
        "data": [tweet2],
        "includes": {"users": [sample_user]},
        "meta": {"result_count": 1},
    }

    responses.add(
        responses.GET,
        "https://api.x.com/2/tweets/search/recent",
        json=page1,
        status=200,
        headers={"x-rate-limit-remaining": "449", "x-rate-limit-reset": "9999999999"},
    )
    responses.add(
        responses.GET,
        "https://api.x.com/2/tweets/search/recent",
        json=page2,
        status=200,
        headers={"x-rate-limit-remaining": "448", "x-rate-limit-reset": "9999999999"},
    )

    client = XApiClient(bearer_token="test_token")
    tweets, users = client.search_all_pages(
        query="#ASCOGU26",
        start_time="2026-02-26T00:00:00Z",
        end_time="2026-02-27T00:00:00Z",
    )

    assert len(tweets) == 2
    assert tweets[0]["id"] == "1234567890123456789"
    assert tweets[1]["id"] == "9999999999999999999"


@responses.activate
def test_search_empty_results():
    """Test handling of empty results."""
    responses.add(
        responses.GET,
        "https://api.x.com/2/tweets/search/recent",
        json={"meta": {"result_count": 0}},
        status=200,
        headers={"x-rate-limit-remaining": "449", "x-rate-limit-reset": "9999999999"},
    )

    client = XApiClient(bearer_token="test_token")
    tweets, users = client.search_all_pages(
        query="#ASCOGU26",
        start_time="2026-02-26T00:00:00Z",
        end_time="2026-02-27T00:00:00Z",
    )

    assert len(tweets) == 0
    assert len(users) == 0
