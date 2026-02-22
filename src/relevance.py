"""Relevance score for ranking tweets by clinical importance.

Score 0-100 that prioritizes:
- KOL curated accounts (+20)
- Clinical content: drugs/tumors (+10 each)
- Discussion quality: replies + quotes (+10)
- Engagement (normalized, up to 40)
- Penalizes pure retweets (-30)
"""

from src.clinical_filters import classify_tweet_text


def compute_relevance_score(
    tweet: dict,
    max_engagement: float = 1.0,
) -> float:
    """Compute relevance score (0-100) for a tweet.

    Args:
        tweet: Dict with tweet fields + user fields (is_curated, etc.)
        max_engagement: Max engagement in the current batch for normalization.

    Returns:
        Float score 0-100.
    """
    # 1. Engagement normalizado (0-40 pts)
    eng = (
        tweet.get("like_count", 0)
        + tweet.get("retweet_count", 0)
        + tweet.get("reply_count", 0)
        + tweet.get("quote_count", 0)
    )
    if max_engagement > 0:
        eng_score = min(40.0, (eng / max_engagement) * 40)
    else:
        eng_score = 0.0

    # 2. Bonus KOL curado (0-20 pts)
    kol_bonus = 20.0 if tweet.get("is_curated") else 0.0

    # 3. Bonus conteudo clinico (0-20 pts)
    clinical = classify_tweet_text(tweet.get("text", ""))
    clinical_bonus = 0.0
    if clinical["drugs"]:
        clinical_bonus += 10.0
    if clinical["tumor_types"]:
        clinical_bonus += 10.0

    # 4. Bonus conversa/thread (0-10 pts)
    thread_bonus = min(
        10.0,
        tweet.get("reply_count", 0) * 2.0 + tweet.get("quote_count", 0) * 3.0,
    )

    # 5. Penalidade retweet puro (-30 pts)
    text = tweet.get("text", "")
    rt_penalty = -30.0 if text.startswith("RT @") else 0.0

    score = eng_score + kol_bonus + clinical_bonus + thread_bonus + rt_penalty
    return round(max(0.0, min(100.0, score)), 1)


def rank_tweets_by_relevance(tweets: list[dict]) -> list[dict]:
    """Sort tweets by relevance score (descending).

    Computes max_engagement from the batch, then scores each tweet.
    Returns tweets with 'relevance_score' and 'clinical_tags' fields added.
    """
    if not tweets:
        return []

    # Compute max engagement for normalization
    max_eng = max(
        (
            t.get("like_count", 0)
            + t.get("retweet_count", 0)
            + t.get("reply_count", 0)
            + t.get("quote_count", 0)
        )
        for t in tweets
    )
    max_eng = max(max_eng, 1)  # avoid division by zero

    for t in tweets:
        t["relevance_score"] = compute_relevance_score(t, max_engagement=max_eng)
        t["clinical_tags"] = classify_tweet_text(t.get("text", ""))

    tweets.sort(key=lambda t: t["relevance_score"], reverse=True)
    return tweets
