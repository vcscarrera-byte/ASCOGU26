"""Feed - All tweets, filterable and searchable."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.components import inject_custom_css, render_tweet_card
from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import count_tweets, get_all_tweets, get_available_dates
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

# Sidebar with full filters
filters = render_sidebar_filters(
    conn,
    show_search=True,
    show_sort=True,
    show_curated=True,
    show_limit=False,
)

# Page size selector in sidebar
page_size = st.sidebar.select_slider(
    "Tweets por pagina",
    options=[10, 20, 50],
    value=20,
)

# Count total matching tweets
total_count = count_tweets(
    conn,
    date=filters["date_filter"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
    text_search=filters["text_search"],
    curated_only=filters["curated_only"],
)

if total_count == 0:
    st.markdown("---")
    st.markdown(":mag: **Nenhum tweet encontrado com esses filtros.**")
    st.markdown("Tente remover alguns filtros ou buscar por outro termo.")
    if st.button("Limpar filtros", type="secondary"):
        st.session_state.clear()
        st.rerun()
    conn.close()
    st.stop()

# Pagination state
total_pages = max(1, (total_count + page_size - 1) // page_size)
if "feed_page" not in st.session_state:
    st.session_state.feed_page = 1
# Clamp to valid range
if st.session_state.feed_page > total_pages:
    st.session_state.feed_page = total_pages
if st.session_state.feed_page < 1:
    st.session_state.feed_page = 1

current_page = st.session_state.feed_page
offset = (current_page - 1) * page_size

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

# Fetch tweets for current page
tweets = get_all_tweets(
    conn,
    date=filters["date_filter"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
    text_search=filters["text_search"],
    limit=page_size,
    offset=offset,
)

# Apply curated filter (post-fetch since count already filtered)
if filters["curated_only"]:
    tweets = [t for t in tweets if t.get("is_curated")]

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

# Count header + pagination info
start_idx = offset + 1
end_idx = min(offset + page_size, total_count)
st.caption(f"Mostrando {start_idx}-{end_idx} de {total_count} tweets")

# Pre-fetch linked abstracts for this page's tweets
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
for i, t in enumerate(tweets, start_idx):
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

# Pagination controls
st.markdown("---")
col_prev, col_info, col_next = st.columns([1, 2, 1])
with col_prev:
    if current_page > 1:
        if st.button("← Anterior"):
            st.session_state.feed_page = current_page - 1
            st.rerun()
with col_info:
    st.markdown(f"<center>Pagina **{current_page}** de **{total_pages}**</center>", unsafe_allow_html=True)
with col_next:
    if current_page < total_pages:
        if st.button("Próxima →"):
            st.session_state.feed_page = current_page + 1
            st.rerun()
