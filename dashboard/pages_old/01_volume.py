"""Volume per day + trends."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_volume_by_day
from src.config import get_db_path
from src.db import create_tables, get_connection

st.set_page_config(page_title="Volume & Trends", layout="wide")
st.title("Volume & Trends")

db_path = get_db_path()
if not db_path.exists():
    st.warning("Database nao encontrada.")
    st.stop()

conn = get_connection(db_path)
create_tables(conn)

# Shared sidebar (no date/curated/limit for volume — just clinical filters)
filters = render_sidebar_filters(
    conn, show_date=False, show_curated=False, show_limit=False,
)

data = get_volume_by_day(
    conn,
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
)
conn.close()

if not data:
    st.info("Nenhum dado coletado ainda.")
    st.stop()

df = pd.DataFrame(data)

# Metric cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tweets", f"{df['tweets'].sum():,}")
col2.metric("Total Engagement", f"{df['engagement'].sum():,}")
col3.metric("Unique Authors", f"{df['authors'].sum():,}")
col4.metric("Days Collected", f"{len(df)}")

# Tweets per day
st.subheader("Tweets por Dia")
fig_tweets = px.bar(
    df, x="date", y="tweets",
    labels={"date": "Data", "tweets": "Tweets"},
    text_auto=True,
)
fig_tweets.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig_tweets, use_container_width=True)

# Engagement per day (stacked)
st.subheader("Engagement por Dia")
fig_eng = go.Figure()
for metric, color, label in [
    ("likes", "#e74c3c", "Likes"),
    ("retweets", "#2ecc71", "Retweets"),
    ("replies", "#3498db", "Replies"),
    ("quotes", "#f39c12", "Quotes"),
]:
    fig_eng.add_trace(go.Bar(x=df["date"], y=df[metric], name=label))
fig_eng.update_layout(barmode="stack", xaxis_tickangle=-45, xaxis_title="Data", yaxis_title="Count")
st.plotly_chart(fig_eng, use_container_width=True)

# Authors per day
st.subheader("Autores Unicos por Dia")
fig_auth = px.line(
    df, x="date", y="authors",
    labels={"date": "Data", "authors": "Autores"},
    markers=True,
)
st.plotly_chart(fig_auth, use_container_width=True)

# Data table
with st.expander("Dados brutos"):
    st.dataframe(df, use_container_width=True)
