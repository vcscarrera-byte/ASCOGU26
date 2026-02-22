"""X API v2 collector: search, paginate, rate-limit, store."""

import hashlib
import logging
import time

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config import X_BEARER_TOKEN, get_api_config, get_collection_config, get_db_path
from src.db import (
    create_collection_run,
    create_tables,
    finish_collection_run,
    get_connection,
    insert_tweet,
    upsert_user,
)
from src.query_builder import build_all_queries

logger = logging.getLogger(__name__)


class RateLimiter:
    """Track API rate limits using response headers."""

    def __init__(self, max_requests: int = 450, window_seconds: int = 900):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.remaining: int | None = None
        self.reset_time: int | None = None

    def update_from_headers(self, headers: dict) -> None:
        if "x-rate-limit-remaining" in headers:
            self.remaining = int(headers["x-rate-limit-remaining"])
        if "x-rate-limit-reset" in headers:
            self.reset_time = int(headers["x-rate-limit-reset"])

    def wait_if_needed(self) -> None:
        if self.remaining is not None and self.remaining <= 1 and self.reset_time:
            sleep_for = max(self.reset_time - int(time.time()), 1) + 1
            logger.warning(f"Rate limit near zero. Sleeping {sleep_for}s until reset.")
            time.sleep(sleep_for)


class XApiClient:
    """Client for X API v2 search endpoints."""

    def __init__(self, bearer_token: str | None = None):
        self.bearer_token = bearer_token or X_BEARER_TOKEN
        if not self.bearer_token:
            raise ValueError("X_BEARER_TOKEN not set. Check your .env file.")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": "ASCOGU26Monitor/1.0",
        })
        self.api_config = get_api_config()
        self.rate_limiter = RateLimiter()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
    )
    def _request(self, url: str, params: dict) -> dict:
        """Make a GET request with retry and rate limit handling."""
        self.rate_limiter.wait_if_needed()

        resp = self.session.get(url, params=params, timeout=30)

        self.rate_limiter.update_from_headers(resp.headers)

        if resp.status_code == 429:
            reset_time = int(resp.headers.get("x-rate-limit-reset", 0))
            sleep_for = max(reset_time - int(time.time()), 1) + 1
            logger.warning(f"429 rate limited. Sleeping {sleep_for}s.")
            time.sleep(sleep_for)
            raise requests.exceptions.Timeout("Rate limited, retrying")

        if resp.status_code >= 400:
            logger.error(f"API error {resp.status_code}: {resp.text[:500]}")
        resp.raise_for_status()
        return resp.json()

    def search_recent(
        self,
        query: str,
        start_time: str,
        end_time: str,
        max_results: int = 100,
        next_token: str | None = None,
    ) -> dict:
        """Call tweets/search/recent with pagination support."""
        url = f"{self.api_config['base_url']}/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "start_time": start_time,
            "end_time": end_time,
            "tweet.fields": self.api_config["tweet_fields"],
            "user.fields": self.api_config["user_fields"],
            "expansions": self.api_config["expansions"],
        }
        if next_token:
            params["next_token"] = next_token

        return self._request(url, params)

    def search_all_pages(
        self,
        query: str,
        start_time: str,
        end_time: str,
    ) -> tuple[list[dict], list[dict]]:
        """Paginate through all results for a query. Returns (tweets, users)."""
        all_tweets: list[dict] = []
        all_users: list[dict] = []
        next_token = None
        page = 0

        while True:
            page += 1
            logger.info(f"  Page {page} for query: {query[:60]}...")

            data = self.search_recent(query, start_time, end_time, next_token=next_token)

            tweets = data.get("data", [])
            users = data.get("includes", {}).get("users", [])
            all_tweets.extend(tweets)
            all_users.extend(users)

            meta = data.get("meta", {})
            logger.info(f"  Got {len(tweets)} tweets (total so far: {meta.get('result_count', 0)})")

            next_token = meta.get("next_token")
            if not next_token:
                break

        return all_tweets, all_users


def collect_daily(date_str: str, start_time: str, end_time: str) -> dict:
    """Run a full daily collection: all queries, all pages, store in DB.

    Args:
        date_str: Date label (e.g. "2026-02-26")
        start_time: ISO8601 start (e.g. "2026-02-26T00:00:00Z")
        end_time: ISO8601 end (e.g. "2026-02-27T00:00:00Z")

    Returns:
        dict with collection stats
    """
    coll_config = get_collection_config()
    db_path = get_db_path()

    # Build queries
    queries = build_all_queries(
        hashtags=coll_config["hashtags"],
        keywords=coll_config.get("keywords"),
        accounts=coll_config["curated_accounts"],
        account_filters=coll_config["account_filters"],
        max_length=coll_config["max_query_length"],
    )
    query_hash = hashlib.sha256("|".join(queries).encode()).hexdigest()[:16]

    logger.info(f"Collecting for {date_str}: {len(queries)} queries, window {start_time} -> {end_time}")

    # DB setup
    conn = get_connection(db_path)
    create_tables(conn)
    run_id = create_collection_run(conn, query_hash, start_time, end_time)

    curated_set = {u.lower() for u in coll_config["curated_accounts"]}
    client = XApiClient()

    total_fetched = 0
    total_new = 0
    seen_tweet_ids: set[str] = set()

    try:
        for i, query in enumerate(queries, 1):
            logger.info(f"Query {i}/{len(queries)}: {query[:80]}...")
            tweets, users = client.search_all_pages(query, start_time, end_time)

            # Upsert users
            for user_data in users:
                upsert_user(conn, user_data, curated_set)

            # Insert tweets (dedup in-memory + DB)
            batch_new = 0
            for tweet in tweets:
                tid = tweet["id"]
                if tid in seen_tweet_ids:
                    continue
                seen_tweet_ids.add(tid)
                total_fetched += 1
                if insert_tweet(conn, tweet, run_id):
                    batch_new += 1

            conn.commit()
            total_new += batch_new
            logger.info(f"  Batch result: {len(tweets)} fetched, {batch_new} new")

        finish_collection_run(conn, run_id, total_fetched, total_new, "completed")
        logger.info(f"Collection done: {total_fetched} fetched, {total_new} new tweets")

    except Exception as e:
        logger.error(f"Collection failed: {e}")
        finish_collection_run(conn, run_id, total_fetched, total_new, "failed", str(e))
        raise
    finally:
        conn.close()

    return {
        "date": date_str,
        "run_id": run_id,
        "queries": len(queries),
        "tweets_fetched": total_fetched,
        "tweets_new": total_new,
    }
