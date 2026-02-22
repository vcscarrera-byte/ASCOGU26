"""Build X API search queries, splitting into batches within the 512-char limit."""


def build_hashtag_query(hashtags: list[str], keywords: list[str] | None = None) -> str:
    """Build query for hashtag search.

    Example output: '#ASCOGU26 OR #ASCOGU2026 OR #ASCOGU OR "ASCO GU 2026"'
    """
    parts = list(hashtags)
    if keywords:
        parts.extend(f'"{kw}"' for kw in keywords)
    return " OR ".join(parts)


def build_account_queries(
    accounts: list[str],
    account_filters: list[str],
    max_length: int = 512,
) -> list[str]:
    """Build batched queries for curated accounts within the char limit.

    Each query: (from:user1 OR from:user2 OR ...) (filter1 OR filter2 OR ...)
    """
    if not accounts:
        return []

    # Build the filter suffix: (prostate OR bladder OR kidney OR ...)
    filter_suffix = " (" + " OR ".join(account_filters) + ")"
    suffix_len = len(filter_suffix)

    # Available chars for from: clauses, accounting for outer parens
    # Format: (from:x OR from:y)<filter_suffix>
    # Outer parens = 2 chars, prefix overhead
    available = max_length - suffix_len - 2  # 2 for outer ()

    queries = []
    current_parts: list[str] = []
    current_len = 0

    for account in accounts:
        part = f"from:{account}"
        # +4 for " OR " separator (except first item)
        added_len = len(part) + (4 if current_parts else 0)

        if current_len + added_len > available and current_parts:
            # Flush current batch
            inner = " OR ".join(current_parts)
            queries.append(f"({inner}){filter_suffix}")
            current_parts = [part]
            current_len = len(part)
        else:
            current_parts.append(part)
            current_len += added_len

    # Flush remaining
    if current_parts:
        inner = " OR ".join(current_parts)
        queries.append(f"({inner}){filter_suffix}")

    return queries


def build_all_queries(
    hashtags: list[str],
    keywords: list[str] | None,
    accounts: list[str],
    account_filters: list[str],
    max_length: int = 512,
) -> list[str]:
    """Build all queries needed for a single collection run.

    Returns a list of query strings, each <= max_length chars.
    """
    queries = []

    # Query 1: hashtag query
    hashtag_q = build_hashtag_query(hashtags, keywords)
    if len(hashtag_q) > max_length:
        # Fallback: just use the primary hashtag
        hashtag_q = hashtags[0]
    queries.append(hashtag_q)

    # Queries 2..N: curated account batches
    account_queries = build_account_queries(accounts, account_filters, max_length)
    queries.extend(account_queries)

    # Validate all queries fit within limit
    for q in queries:
        assert len(q) <= max_length, f"Query exceeds {max_length} chars ({len(q)}): {q[:80]}..."

    return queries
