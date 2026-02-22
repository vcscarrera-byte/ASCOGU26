"""HOME - Content-first: posts primeiro, brief e metricas no final."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.components import (
    inject_custom_css,
    render_brief_section,
    render_mini_stats,
    render_tweet_card,
)
from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates, get_quick_stats, get_top_tweets
from src.config import get_db_path
from src.db import create_tables, get_connection, get_daily_brief
from src.relevance import rank_tweets_by_relevance

st.set_page_config(page_title="Hoje | ASCO GU 2026", page_icon=":microscope:", layout="wide")
inject_custom_css()

# Header
st.title(":microscope: ASCO GU 2026 — Hoje")

db_path = get_db_path()
if not db_path.exists():
    st.warning("Database nao encontrada. Execute uma coleta primeiro.")
    st.stop()

conn = get_connection(db_path)
create_tables(conn)

dates = get_available_dates(conn)
if not dates:
    st.info("Nenhum dado coletado. Execute `python scripts/collect.py --date today`")
    conn.close()
    st.stop()

# Sidebar: date + clinical filters
filters = render_sidebar_filters(
    conn,
    show_date=True,
    show_curated=True,
    show_limit=False,
    show_search=False,
    show_sort=False,
)

# Language selector (small, top right)
lang = st.radio("Idioma do brief", ["PT-BR", "EN"], horizontal=True, label_visibility="collapsed")
lang_code = "pt" if lang == "PT-BR" else "en"

# date_filter = None means "Todos os dias" — pass None to queries so they aggregate all
selected_date = filters["date_filter"]
# For brief we need a specific date — use most recent
brief_date = selected_date or dates[-1]

# Quick stats (1 subtle line) — uses None for all dates
stats = get_quick_stats(conn, date=selected_date)
render_mini_stats(
    total_tweets=stats["total_tweets"],
    unique_authors=stats["unique_authors"],
    total_engagement=stats["total_engagement"],
    curated_active=stats["curated_active"],
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POSTS PRIMEIRO — o que o médico quer ver
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
period_label = f"do dia {selected_date}" if selected_date else "de todos os dias"
st.subheader(f"Top Posts {period_label}")

has_clinical_filter = bool(filters["selected_tumors"] or filters["selected_drugs"])

tweets = get_top_tweets(
    conn,
    date=selected_date,  # None = all dates
    limit=50,
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
)

if filters["curated_only"]:
    tweets = [t for t in tweets if t.get("is_curated")]

if tweets:
    ranked = rank_tweets_by_relevance(tweets)

    # Show filter context
    filter_parts = []
    if has_clinical_filter:
        active = []
        if filters["selected_tumors"]:
            active.extend(filters["selected_tumors"])
        if filters["selected_drugs"]:
            active.extend(filters["selected_drugs"])
        filter_parts.append(f"Filtrando por: {', '.join(active)}")
    filter_parts.append(f"{len(ranked)} posts encontrados")
    st.caption(" — ".join(filter_parts))

    # Show all ranked posts (content is king)
    for i, t in enumerate(ranked[:15], 1):
        render_tweet_card(t, rank=i, show_relevance=True)

    if len(ranked) > 15:
        with st.expander(f"Ver mais {len(ranked) - 15} posts"):
            for i, t in enumerate(ranked[15:], 16):
                render_tweet_card(t, rank=i, compact=True)
else:
    if has_clinical_filter:
        st.info("Nenhum post encontrado com esses filtros. Tente ampliar a busca.")
    else:
        st.info("Nenhum tweet para esta data.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BRIEF DO DIA — resumo IA (colapsável, embaixo dos posts)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
with st.expander(f"Resumo do Dia — {brief_date} (gerado por IA)", expanded=False):
    brief = get_daily_brief(conn, brief_date, lang_code)
    if brief:
        render_brief_section(brief)
    else:
        st.info(f"Brief nao gerado para {brief_date}.")
        # Only show generate button if API key is available (not on public deploy)
        import os
        if os.environ.get("ANTHROPIC_API_KEY"):
            if st.button("Gerar Brief Agora"):
                with st.spinner("Gerando brief via Claude API..."):
                    try:
                        from src.summarizer import generate_brief
                        new_brief = generate_brief(conn, brief_date, lang_code)
                        st.success("Brief gerado!")
                        render_brief_section(new_brief)
                    except Exception as e:
                        st.error(f"Erro: {e}")

conn.close()
