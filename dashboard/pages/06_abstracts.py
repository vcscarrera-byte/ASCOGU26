"""Abstracts - Browse and filter 892+ ASCO GU 2026 abstracts."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.components import inject_custom_css, render_abstract_card, render_tweet_card
from dashboard.sidebar_filters import render_sidebar_filters
from src.abstract_aggregator import get_abstract_stats, get_all_abstracts
from src.config import get_db_path
from src.db import create_tables, get_connection, get_linked_tweets

st.set_page_config(page_title="Abstracts | ASCO GU RADAR", page_icon=":satellite:", layout="wide")
inject_custom_css()
st.title(":microscope: Abstracts — ASCO GU 2026")

db_path = get_db_path()
if not db_path.exists():
    st.warning("Database nao encontrada.")
    st.stop()

conn = get_connection(db_path)
create_tables(conn)

# Check if abstracts exist
abs_count = conn.execute("SELECT COUNT(*) FROM abstracts").fetchone()[0]
if not abs_count:
    st.info(
        "Nenhum abstract importado. Execute:\n\n"
        "`python scripts/import_abstracts.py`"
    )
    conn.close()
    st.stop()

# Quick stats bar
stats = get_abstract_stats(conn)
session_parts = []
for stype, cnt in list(stats["by_session_type"].items())[:4]:
    short = stype.replace(" Session", "").replace(" Abstract", "")
    session_parts.append(f"**{cnt}** {short}")
stat_line = f"**{stats['total']}** abstracts · " + " · ".join(session_parts)
if stats["with_buzz"]:
    stat_line += f" · **{stats['with_buzz']}** com tweets"
st.caption(stat_line)

# Sidebar: session type + clinical filters + search + sort
filters = render_sidebar_filters(
    conn,
    show_date=False,
    show_curated=False,
    show_search=True,
    show_sort=True,
    show_session_type=True,
    show_limit=True,
    default_limit=30,
    max_limit=100,
)

# Map sort options for abstracts
sort_map = {
    "relevance": "session_rank",
    "engagement": "buzz",
    "recent": "number",
}
abs_sort = sort_map.get(filters["sort_by"], "session_rank")

# Query
abstracts = get_all_abstracts(
    conn,
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
    session_types=filters["selected_session_types"],
    text_search=filters["text_search"],
    sort_by=abs_sort,
    limit=filters["limit"],
)

if not abstracts:
    st.info("Nenhum abstract encontrado com esses filtros.")
    conn.close()
    st.stop()

# Filter context
st.caption(f"{len(abstracts)} abstracts encontrados")

st.markdown("---")

# Render abstract cards
for i, a in enumerate(abstracts, 1):
    render_abstract_card(a, rank=i)

    # Expandable detail
    with st.expander(f"Detalhe — #{a['abstract_number']}"):
        # Body text
        body = a.get("body", "").strip()
        if body and "full, final text" not in body.lower():
            st.markdown(f'<div class="tweet-text">\n\n{body}\n\n</div>', unsafe_allow_html=True)
        else:
            st.info("Texto completo sera liberado em 23/fev 17h EST.")

        # Metadata
        cols = st.columns(2)
        with cols[0]:
            if a.get("presenter"):
                st.markdown(f"**Apresentador:** {a['presenter']}")
            if a.get("session_title"):
                st.markdown(f"**Sessao:** {a['session_title']}")
            if a.get("genes"):
                st.markdown(f"**Genes:** {a['genes']}")
        with cols[1]:
            if a.get("subjects"):
                st.markdown(f"**Assuntos:** {a['subjects']}")
            if a.get("organizations"):
                st.markdown(f"**Instituicoes:** {a['organizations']}")
            if a.get("countries"):
                st.markdown(f"**Paises:** {a['countries']}")

        # Linked tweets
        linked = get_linked_tweets(conn, a["abstract_number"])
        if linked:
            st.markdown(f"**{len(linked)} tweets linkados:**")
            for t in linked[:5]:
                render_tweet_card(t, compact=True)

        # Link to ASCO
        if a.get("url"):
            st.markdown(f"[:link: **Ver no site da ASCO**]({a['url']})")

conn.close()
