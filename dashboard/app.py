"""ASCO GU RADAR 2026 — Home (hero + today highlights)."""

import os
import sys
from pathlib import Path

import streamlit as st

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(
    page_title="ASCO GU RADAR 2026",
    page_icon=":satellite:",
    layout="wide",
)

from dashboard.components import (
    inject_custom_css,
    render_abstract_card,
    render_brief_section,
    render_mini_stats,
    render_tweet_card,
)
from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates, get_quick_stats, get_top_tweets
from src.config import get_db_path
from src.db import create_tables, get_connection, get_daily_brief
from src.relevance import rank_tweets_by_relevance

inject_custom_css()
st.logo(":satellite: ASCO GU RADAR 2026")

# ── Hero ──
st.title(":satellite: ASCO GU RADAR")
st.caption("2026")
st.markdown("*Destaques dos KOLs de uro-oncologia no ASCO GU 2026, ranqueados por relevancia clinica.*")

# ── Data check ──
db_path = get_db_path()
if not db_path.exists():
    st.warning("Database not found. Run a collection first.")
    st.stop()

conn = get_connection(db_path)
create_tables(conn)

dates = get_available_dates(conn)
if not dates:
    st.info("No tweets collected yet. Run `python scripts/collect.py --date today` to start.")
    conn.close()
    st.stop()

# ── Quick stats ──
st.markdown("---")

row = conn.execute("SELECT COUNT(*) as cnt FROM tweets").fetchone()
total_tweets = row["cnt"]
row = conn.execute("SELECT COUNT(DISTINCT author_id) as cnt FROM tweets").fetchone()
total_authors = row["cnt"]
row = conn.execute(
    "SELECT COUNT(DISTINCT author_id) as cnt FROM tweets "
    "WHERE author_id IN (SELECT user_id FROM users WHERE is_curated = 1)"
).fetchone()
curated_active = row["cnt"]

try:
    total_abstracts = conn.execute("SELECT COUNT(*) FROM abstracts").fetchone()[0]
except Exception:
    total_abstracts = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Tweets", f"{total_tweets:,}")
col2.metric("Autores", f"{total_authors:,}")
col3.metric("KOLs Ativos", f"{curated_active:,}")
col4.metric("Abstracts", f"{total_abstracts:,}")

# ── Sidebar filters ──
filters = render_sidebar_filters(
    conn,
    show_date=True,
    show_curated=True,
    show_limit=False,
    show_search=False,
    show_sort=False,
)

# Language selector
lang = st.radio("Idioma do brief", ["PT-BR", "EN"], horizontal=True, label_visibility="collapsed")
lang_code = "pt" if lang == "PT-BR" else "en"

selected_date = filters["date_filter"]
brief_date = selected_date or dates[-1]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TOP POSTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
period_label = f"do dia {selected_date}" if selected_date else "de todos os dias"
st.subheader(f"Top Posts {period_label}")

has_clinical_filter = bool(filters["selected_tumors"] or filters["selected_drugs"])

tweets = get_top_tweets(
    conn,
    date=selected_date,
    limit=50,
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
)

if filters["curated_only"]:
    tweets = [t for t in tweets if t.get("is_curated")]

if tweets:
    ranked = rank_tweets_by_relevance(tweets)

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
# ABSTRACTS EM DESTAQUE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    abs_count = conn.execute("SELECT COUNT(*) FROM abstracts").fetchone()[0]
except Exception:
    abs_count = 0

if abs_count > 0:
    st.markdown("---")
    st.subheader(":page_facing_up: Abstracts em Destaque")

    try:
        from src.abstract_aggregator import get_abstracts_with_buzz, get_all_abstracts

        buzz_abstracts = get_abstracts_with_buzz(conn, min_tweets=1, limit=5)
        if buzz_abstracts:
            st.caption("Abstracts mais discutidos nos tweets")
            for i, a in enumerate(buzz_abstracts, 1):
                render_abstract_card(a, rank=i, compact=True)
        else:
            top_abstracts = get_all_abstracts(
                conn,
                session_types=["Oral Abstract Session", "Rapid Oral Abstract Session"],
                selected_tumors=filters["selected_tumors"] or None,
                selected_drugs=filters["selected_drugs"] or None,
                sort_by="session_rank",
                limit=5,
            )
            if top_abstracts:
                st.caption("Abstracts em sessoes orais (Oral + Rapid Oral)")
                for i, a in enumerate(top_abstracts, 1):
                    render_abstract_card(a, rank=i, compact=True)
            else:
                st.caption("Nenhum abstract oral encontrado com os filtros atuais.")
    except Exception:
        pass

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BRIEF DO DIA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
st.markdown("---")
with st.expander(f"Resumo do Dia — {brief_date} (gerado por IA)", expanded=False):
    brief = get_daily_brief(conn, brief_date, lang_code)
    if brief:
        render_brief_section(brief)
    else:
        st.info(f"Brief nao gerado para {brief_date}.")
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
