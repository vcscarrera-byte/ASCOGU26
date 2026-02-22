"""Feed - All tweets, filterable and searchable."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.components import inject_custom_css, render_tweet_card
from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_all_tweets, get_available_dates
from src.config import get_db_path
from src.db import create_tables, get_connection
from src.relevance import rank_tweets_by_relevance

st.set_page_config(page_title="Feed | ASCO GU 2026", layout="wide")
inject_custom_css()
st.title(":scroll: Feed")

db_path = get_db_path()
if not db_path.exists():
    st.warning("Database nao encontrada.")
    st.stop()

conn = get_connection(db_path)
create_tables(conn)

dates = get_available_dates(conn)
if not dates:
    st.info("Nenhum dado coletado ainda.")
    conn.close()
    st.stop()

# Sidebar with full filters
filters = render_sidebar_filters(
    conn,
    show_search=True,
    show_sort=True,
    show_curated=True,
    show_limit=True,
    default_limit=30,
    max_limit=100,
)

# Fetch tweets
tweets = get_all_tweets(
    conn,
    date=filters["date_filter"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
    text_search=filters["text_search"],
    limit=filters["limit"],
)
conn.close()

# Apply curated filter
if filters["curated_only"]:
    tweets = [t for t in tweets if t.get("is_curated")]

if not tweets:
    st.info("Nenhum tweet encontrado com esses filtros.")
    st.stop()

# Sort
if filters["sort_by"] == "relevance":
    tweets = rank_tweets_by_relevance(tweets)
elif filters["sort_by"] == "engagement":
    tweets.sort(
        key=lambda t: t.get("like_count", 0) + t.get("retweet_count", 0) + t.get("reply_count", 0) + t.get("quote_count", 0),
        reverse=True,
    )
elif filters["sort_by"] == "recent":
    tweets.sort(key=lambda t: t.get("created_at", ""), reverse=True)

# Count header
st.caption(f"Mostrando {len(tweets)} tweets")

# Render tweets
for i, t in enumerate(tweets, 1):
    render_tweet_card(
        t,
        rank=i if filters["sort_by"] != "recent" else None,
        compact=True,
        show_relevance=filters["sort_by"] == "relevance",
    )
