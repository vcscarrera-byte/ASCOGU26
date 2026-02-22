"""Topic clustering for tweets using TF-IDF + KMeans."""

import logging
import re
import sqlite3

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from src.clinical_filters import build_text_filter_clause
from src.config import get_topic_config

logger = logging.getLogger(__name__)


def preprocess_tweet(text: str, stop_words: list[str] | None = None) -> str:
    """Clean tweet text for topic modeling."""
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove mentions
    text = re.sub(r"@\w+", "", text)
    # Keep hashtag text but remove #
    text = re.sub(r"#(\w+)", r"\1", text)
    # Remove RT prefix
    text = re.sub(r"^RT\s+", "", text)
    # Lowercase
    text = text.lower()
    # Remove domain stop words
    if stop_words:
        for sw in stop_words:
            text = re.sub(rf"\b{re.escape(sw.lower())}\b", "", text)
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def cluster_tweets(
    tweets: list[dict],
    n_clusters: int | None = None,
    stop_words: list[str] | None = None,
    min_cluster_size: int = 5,
) -> tuple[list[int], dict[int, list[str]], list[str]]:
    """Cluster tweets into topics.

    Args:
        tweets: List of dicts with at least a 'text' field
        n_clusters: Number of clusters (auto from config if None)
        stop_words: Extra domain stop words
        min_cluster_size: Minimum useful cluster size

    Returns:
        (labels, cluster_topics, processed_texts)
        - labels: cluster label per tweet
        - cluster_topics: {cluster_id: [top_terms]}
        - processed_texts: cleaned texts
    """
    config = get_topic_config()
    if n_clusters is None:
        n_clusters = config.get("num_topics", 8)
    if stop_words is None:
        stop_words = config.get("stop_words_extra", [])

    texts = [preprocess_tweet(t["text"], stop_words) for t in tweets]

    # Filter out empty texts
    valid = [(i, t) for i, t in enumerate(texts) if len(t) > 10]
    if len(valid) < n_clusters * min_cluster_size:
        n_clusters = max(2, len(valid) // min_cluster_size)

    if len(valid) < 4:
        logger.warning("Too few tweets for clustering")
        return [0] * len(tweets), {0: ["insufficient_data"]}, texts

    valid_indices, valid_texts = zip(*valid)

    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=2,
        max_df=0.95,
        ngram_range=(1, 2),
        stop_words="english",
    )

    try:
        tfidf_matrix = vectorizer.fit_transform(valid_texts)
    except ValueError:
        logger.warning("TF-IDF failed (likely too few unique terms)")
        return [0] * len(tweets), {0: ["insufficient_data"]}, texts

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    valid_labels = km.fit_predict(tfidf_matrix)

    # Map back to full tweet list
    labels = [-1] * len(tweets)
    for idx, label in zip(valid_indices, valid_labels):
        labels[idx] = int(label)

    # Extract top terms per cluster
    feature_names = vectorizer.get_feature_names_out()
    cluster_topics: dict[int, list[str]] = {}
    for i in range(n_clusters):
        center = km.cluster_centers_[i]
        top_indices = center.argsort()[-10:][::-1]
        cluster_topics[i] = [feature_names[j] for j in top_indices]

    logger.info(f"Clustered {len(valid)} tweets into {n_clusters} topics")
    return labels, cluster_topics, texts


def get_tweets_for_clustering(
    conn: sqlite3.Connection,
    date: str | None = None,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
) -> list[dict]:
    """Fetch tweets for topic modeling, excluding pure retweets."""
    query = """
        SELECT t.tweet_id, t.text, t.author_id, t.created_at,
               (t.like_count + t.retweet_count + t.reply_count + t.quote_count) as engagement,
               u.username, u.name
        FROM tweets t
        JOIN users u ON t.author_id = u.user_id
        WHERE t.text NOT LIKE 'RT @%%'
    """
    params: list = []
    if date:
        query += " AND DATE(t.created_at) = ?"
        params.append(date)

    filter_clause, filter_params = build_text_filter_clause(
        selected_tumors, selected_drugs, text_column="t.text",
    )
    if filter_clause:
        query += f" AND {filter_clause}"
        params.extend(filter_params)

    query += " ORDER BY engagement DESC"

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def cluster_and_summarize(
    conn: sqlite3.Connection,
    date: str | None = None,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
) -> tuple[list[dict], dict[int, list[str]]]:
    """Full pipeline: fetch tweets, cluster, return annotated tweets + topics.

    Returns:
        (tweets_with_labels, cluster_topics)
    """
    tweets = get_tweets_for_clustering(conn, date, selected_tumors, selected_drugs)
    if not tweets:
        return [], {}

    labels, cluster_topics, _ = cluster_tweets(tweets)

    for tweet, label in zip(tweets, labels):
        tweet["topic_id"] = label
        tweet["topic_terms"] = cluster_topics.get(label, [])

    return tweets, cluster_topics
