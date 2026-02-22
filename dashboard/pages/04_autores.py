"""Autores - KOL ranking and profiles."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.components import inject_custom_css
from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates, get_top_authors
from src.config import get_db_path
from src.db import create_tables, get_connection

st.set_page_config(page_title="Autores | ASCO GU 2026", layout="wide")
inject_custom_css()
st.title(":bust_in_silhouette: Autores")

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

# Sidebar
filters = render_sidebar_filters(conn, show_curated=True, show_search=False)

authors = get_top_authors(
    conn,
    date=filters["date_filter"],
    limit=filters["limit"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
)
conn.close()

if filters["curated_only"]:
    authors = [a for a in authors if a.get("is_curated")]

if not authors:
    st.info("Nenhum autor encontrado com esses filtros.")
    st.stop()

# Author cards
for i, a in enumerate(authors, 1):
    with st.container():
        col_rank, col_info, col_stats = st.columns([1, 5, 4])

        with col_rank:
            st.markdown(f"### #{i}")

        with col_info:
            curated = " :star:" if a.get("is_curated") else ""
            st.markdown(f"**{a['name']}** (@{a['username']}){curated}")
            profile_url = f"https://x.com/{a['username']}"
            followers = a.get("followers_count", 0)
            st.caption(
                f"{followers:,} seguidores · "
                f"[Perfil no X]({profile_url})"
            )

        with col_stats:
            scol1, scol2, scol3 = st.columns(3)
            scol1.metric("Tweets", a.get("tweet_count", 0))
            scol2.metric("Engagement", f"{a.get('total_engagement', 0):,}")
            scol3.metric("Eng/Tweet", f"{a.get('avg_engagement', 0):.0f}")

        st.divider()

# Summary chart
st.subheader("Engagement por Autor")
df = pd.DataFrame(authors)
df["label"] = df.apply(
    lambda r: f"@{r['username']}" + (" *" if r.get("is_curated") else ""), axis=1
)

fig = px.bar(
    df.head(filters["limit"]),
    x="label",
    y="total_engagement",
    color="is_curated",
    color_discrete_map={0: "#95a5a6", 1: "#e74c3c", False: "#95a5a6", True: "#e74c3c"},
    labels={"label": "Autor", "total_engagement": "Engagement", "is_curated": "KOL Curado"},
    text_auto=True,
)
fig.update_layout(xaxis_tickangle=-45, showlegend=False, height=400)
st.plotly_chart(fig, use_container_width=True)
