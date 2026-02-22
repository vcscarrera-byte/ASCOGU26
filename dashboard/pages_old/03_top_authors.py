"""Top authors leaderboard."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates, get_top_authors
from src.config import get_db_path
from src.db import create_tables, get_connection

st.set_page_config(page_title="Top Authors", layout="wide")
st.title("Top Autores")

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

# Shared sidebar
filters = render_sidebar_filters(conn, show_curated=False)

authors = get_top_authors(
    conn,
    date=filters["date_filter"],
    limit=filters["limit"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
)
conn.close()

if not authors:
    st.info("Nenhum autor encontrado com esses filtros.")
    st.stop()

df = pd.DataFrame(authors)
df["label"] = df.apply(
    lambda r: f"@{r['username']}" + (" *" if r["is_curated"] else ""), axis=1
)

# Bar chart
st.subheader("Engagement por Autor")
fig = px.bar(
    df.head(filters["limit"]),
    x="label",
    y="total_engagement",
    color="is_curated",
    color_discrete_map={0: "#95a5a6", 1: "#e74c3c"},
    labels={"label": "Autor", "total_engagement": "Engagement Total", "is_curated": "Curated"},
    text_auto=True,
)
fig.update_layout(xaxis_tickangle=-45, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# Table
st.subheader("Tabela")
display_df = df[["username", "name", "tweet_count", "total_engagement", "avg_engagement", "followers_count", "is_curated"]].copy()
display_df.columns = ["Username", "Nome", "Tweets", "Engagement", "Eng. Medio", "Seguidores", "Curated"]
display_df["Curated"] = display_df["Curated"].map({1: "Sim", 0: ""})
display_df["Eng. Medio"] = display_df["Eng. Medio"].round(1)
display_df.index = range(1, len(display_df) + 1)
st.dataframe(display_df, use_container_width=True)
