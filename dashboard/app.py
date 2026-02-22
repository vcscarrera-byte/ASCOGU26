"""ASCO GU 2026 - Twitter/X Monitor Dashboard."""

import sys
from pathlib import Path

import streamlit as st

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

st.set_page_config(
    page_title="ASCO GU 2026 Monitor",
    page_icon=":microscope:",
    layout="wide",
)

st.title(":microscope: ASCO GU 2026 Monitor")
st.markdown(
    "Monitoramento de tweets do **ASCO Genitourinary Cancers Symposium 2026** "
    "(26-28 fev, San Francisco)."
)

st.sidebar.markdown("### Navegacao")
st.sidebar.markdown(
    "- **Hoje** — Resumo do dia + top posts\n"
    "- **Feed** — Todos os posts com filtros\n"
    "- **Temas** — Clusters tematicos\n"
    "- **Autores** — Ranking de KOLs\n"
    "- **Metricas** — Volume e trends"
)

# Show quick stats if data exists
from src.config import get_db_path
from src.db import create_tables, get_connection

db_path = get_db_path()
if db_path.exists():
    conn = get_connection(db_path)
    create_tables(conn)

    row = conn.execute("SELECT COUNT(*) as cnt FROM tweets").fetchone()
    total_tweets = row["cnt"]
    row = conn.execute("SELECT COUNT(DISTINCT author_id) as cnt FROM tweets").fetchone()
    total_authors = row["cnt"]
    row = conn.execute(
        "SELECT COUNT(DISTINCT author_id) as cnt FROM tweets "
        "WHERE author_id IN (SELECT user_id FROM users WHERE is_curated = 1)"
    ).fetchone()
    curated_active = row["cnt"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tweets", f"{total_tweets:,}")
    col2.metric("Autores Unicos", f"{total_authors:,}")
    col3.metric("KOLs Ativos", f"{curated_active:,}")

    if total_tweets == 0:
        st.info(
            "Nenhum tweet coletado ainda. "
            "Execute `python scripts/collect.py --date today` para comecar."
        )
    else:
        st.success("Use a aba **Hoje** para ver o resumo do dia.")

    conn.close()
else:
    st.warning("Database nao encontrada. Execute uma coleta primeiro.")
