"""Tweet endpoints."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/top")
def get_top_tweets(
    limit: int = Query(20, ge=1, le=100),
    tumors: str | None = Query(None, description="Comma-separated tumor types"),
    drugs: str | None = Query(None, description="Comma-separated drug names"),
):
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.aggregator import get_top_tweets as _get_top
    from src.relevance import rank_tweets_by_relevance
    from src.clinical_filters import classify_tweet_text

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    selected_tumors = [t.strip() for t in tumors.split(",")] if tumors else None
    selected_drugs = [d.strip() for d in drugs.split(",")] if drugs else None

    tweets = _get_top(conn, limit=limit, selected_tumors=selected_tumors, selected_drugs=selected_drugs)
    ranked = rank_tweets_by_relevance(tweets)

    for t in ranked:
        if "clinical_tags" not in t:
            t["clinical_tags"] = classify_tweet_text(t.get("text", ""))

    conn.close()
    return {"tweets": ranked, "total": len(ranked)}


@router.get("")
def get_all_tweets(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query("relevance", pattern="^(relevance|engagement|recent)$"),
    tumors: str | None = None,
    drugs: str | None = None,
    curated: bool = False,
):
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.aggregator import get_all_tweets as _get_all, count_tweets
    from src.relevance import rank_tweets_by_relevance
    from src.clinical_filters import classify_tweet_text

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    selected_tumors = [t.strip() for t in tumors.split(",")] if tumors else None
    selected_drugs = [d.strip() for d in drugs.split(",")] if drugs else None

    total = count_tweets(conn, selected_tumors=selected_tumors, selected_drugs=selected_drugs,
                         text_search=search, curated_only=curated)
    offset = (page - 1) * size
    tweets = _get_all(conn, selected_tumors=selected_tumors, selected_drugs=selected_drugs,
                      text_search=search, limit=size, offset=offset)

    if curated:
        tweets = [t for t in tweets if t.get("is_curated")]

    if sort == "relevance":
        tweets = rank_tweets_by_relevance(tweets)
    elif sort == "engagement":
        tweets.sort(key=lambda t: sum(t.get(k, 0) for k in ["like_count", "retweet_count", "reply_count", "quote_count"]), reverse=True)

    for t in tweets:
        if "clinical_tags" not in t:
            t["clinical_tags"] = classify_tweet_text(t.get("text", ""))

    conn.close()
    return {
        "tweets": tweets,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": max(1, (total + size - 1) // size),
    }


@router.get("/{tweet_id}/abstracts")
def get_tweet_abstracts(tweet_id: str):
    from src.config import get_db_path
    from src.db import get_connection, create_tables, get_linked_abstracts

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)
    linked = get_linked_abstracts(conn, tweet_id)
    conn.close()
    return {"abstracts": linked}
