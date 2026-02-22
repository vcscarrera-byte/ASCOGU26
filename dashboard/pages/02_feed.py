"""Feed - All tweets, filterable and searchable."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.components import inject_custom_css, render_tweet_card
from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_all_tweets, get_available_dates
from src.config import get_db_path
from src.db import create_tables, get_connection, get_linked_abstracts
from src.relevance import rank_tweets_by_relevance

st.set_page_config(page_title="Principais postagens | ASCO GU RADAR", page_icon=":satellite:", layout="wide")
inject_custom_css()
st.title(":newspaper: Principais postagens")

db_path = get_db_path()
if not db_path.exists():
    st.warning(":construction: Base de dados nao encontrada.")
    st.stop()

conn = get_connection(db_path)
create_tables(conn)

dates = get_available_dates(conn)
if not dates:
    st.info(":inbox_tray: Nenhum dado coletado ainda.")
    conn.close()
    st.stop()

# Sidebar with full filters (no limit — show all)
filters = render_sidebar_filters(
    conn,
    show_search=True,
    show_sort=True,
    show_curated=True,
    show_limit=False,
)

# Fetch tweets
tweets = get_all_tweets(
    conn,
    date=filters["date_filter"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
    text_search=filters["text_search"],
    limit=9999,
)

# Apply curated filter
if filters["curated_only"]:
    tweets = [t for t in tweets if t.get("is_curated")]

if not tweets:
    st.markdown("---")
    st.markdown(":mag: **Nenhum tweet encontrado com esses filtros.**")
    st.markdown("Tente remover alguns filtros ou buscar por outro termo.")
    if st.button("Limpar filtros", type="secondary"):
        st.session_state.clear()
        st.rerun()
    st.stop()

# Inline sort bar
sort_selection = st.segmented_control(
    "Ordenar",
    options=["Relevância", "Engagement", "Recentes"],
    default="Relevância",
    label_visibility="collapsed",
)
sort_map = {
    "Relevância": "relevance",
    "Engagement": "engagement",
    "Recentes": "recent",
}
active_sort = sort_map.get(sort_selection, "relevance")

# Sort
if active_sort == "relevance":
    tweets = rank_tweets_by_relevance(tweets)
elif active_sort == "engagement":
    tweets.sort(
        key=lambda t: t.get("like_count", 0) + t.get("retweet_count", 0) + t.get("reply_count", 0) + t.get("quote_count", 0),
        reverse=True,
    )
elif active_sort == "recent":
    tweets.sort(key=lambda t: t.get("created_at", ""), reverse=True)

# Count header
st.caption(f"Mostrando {len(tweets)} tweets")

# Pre-fetch linked abstracts for all tweets (batch-friendly)
try:
    _linked_cache = {}
    for t in tweets:
        tid = t.get("tweet_id", "")
        if tid:
            linked = get_linked_abstracts(conn, tid)
            if linked:
                _linked_cache[tid] = linked
except Exception:
    _linked_cache = {}

conn.close()

# Render tweets
for i, t in enumerate(tweets, 1):
    # Show linked abstract badges before the card
    tid = t.get("tweet_id", "")
    linked_abs = _linked_cache.get(tid, [])
    if linked_abs:
        abs_badges = " ".join(
            f":violet-background[Abs #{la['abstract_number']}]" for la in linked_abs
        )
        st.markdown(abs_badges)

    render_tweet_card(
        t,
        rank=i if active_sort != "recent" else None,
        compact=True,
        show_relevance=active_sort == "relevance",
    )
