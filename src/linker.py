"""Link tweets to abstracts by regex matching of abstract numbers in tweet text."""

import logging
import re
import sqlite3

from src.db import link_tweet_to_abstract

logger = logging.getLogger(__name__)

# Patterns ordered by confidence (high to low)
PATTERNS: list[tuple[re.Pattern, float, bool]] = [
    # "Abstract 305", "Abs 305", "abstract #305" — high confidence
    (re.compile(r"(?:abstract|abs)[\s#]+(\d{2,4})\b", re.IGNORECASE), 1.0, False),
    # "#305" bare number — requires ASCO/GU context in same tweet
    (re.compile(r"#(\d{3,4})\b"), 0.8, True),
]

CONTEXT_PATTERN = re.compile(
    r"(?:asco|gu26|ascogu|gu2026|gu\s*26|asco\s*gu)",
    re.IGNORECASE,
)


def _has_asco_context(text: str) -> bool:
    """Check if tweet text contains ASCO GU conference context."""
    return bool(CONTEXT_PATTERN.search(text))


def find_abstract_numbers(text: str) -> list[tuple[str, float]]:
    """Find abstract number mentions in text.

    Returns list of (abstract_number, confidence) tuples.
    """
    results: dict[str, float] = {}

    for pattern, confidence, needs_context in PATTERNS:
        if needs_context and not _has_asco_context(text):
            continue
        for match in pattern.finditer(text):
            num = match.group(1)
            # Keep highest confidence per number
            if num not in results or confidence > results[num]:
                results[num] = confidence

    return list(results.items())


def link_tweets_to_abstracts(conn: sqlite3.Connection) -> int:
    """Scan all tweets for abstract number mentions and create links.

    Only creates links for abstract numbers that exist in the abstracts table.
    Returns the number of new links created.
    """
    # Get set of valid abstract numbers
    rows = conn.execute("SELECT abstract_number FROM abstracts").fetchall()
    valid_numbers = {r["abstract_number"] for r in rows}

    if not valid_numbers:
        logger.warning("No abstracts in DB — skipping linking")
        return 0

    # Get all tweets
    tweet_rows = conn.execute("SELECT tweet_id, text FROM tweets").fetchall()

    new_links = 0
    for tweet in tweet_rows:
        mentions = find_abstract_numbers(tweet["text"])
        for abstract_num, confidence in mentions:
            if abstract_num in valid_numbers:
                created = link_tweet_to_abstract(
                    conn,
                    tweet_id=tweet["tweet_id"],
                    abstract_number=abstract_num,
                    match_type="auto",
                    confidence=confidence,
                )
                if created:
                    new_links += 1

    conn.commit()
    logger.info(f"Created {new_links} tweet-abstract links")
    return new_links
