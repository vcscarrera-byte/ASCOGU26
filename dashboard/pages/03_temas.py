"""Temas - Topic clusters with representative posts."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.components import inject_custom_css, render_tweet_card
from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates
from src.config import get_db_path
from src.db import create_tables, get_connection
from src.topic_model import cluster_and_summarize

st.set_page_config(page_title="Temas | ASCO GU 2026", layout="wide")
inject_custom_css()
st.title(":label: Temas")

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

# Sidebar (date + clinical filters)
filters = render_sidebar_filters(conn, show_curated=False, show_limit=False)

with st.spinner("Analisando temas..."):
    tweets, cluster_topics = cluster_and_summarize(
        conn,
        date=filters["date_filter"],
        selected_tumors=filters["selected_tumors"],
        selected_drugs=filters["selected_drugs"],
    )

conn.close()

if not tweets or not cluster_topics:
    st.info("Poucos tweets para agrupar temas com esses filtros.")
    st.stop()

# Build topic stats
topic_data = {}
for t in tweets:
    tid = t.get("topic_id", -1)
    if tid < 0:
        continue
    if tid not in topic_data:
        topic_data[tid] = {"tweets": [], "engagement": 0}
    topic_data[tid]["tweets"].append(t)
    topic_data[tid]["engagement"] += t.get("engagement", 0)

# Sort topics by tweet count
sorted_topics = sorted(
    cluster_topics.items(),
    key=lambda x: len(topic_data.get(x[0], {}).get("tweets", [])),
    reverse=True,
)

# Overview chart
summary = []
for tid, terms in sorted_topics:
    data = topic_data.get(tid, {"tweets": [], "engagement": 0})
    summary.append({
        "Tema": ", ".join(terms[:4]),
        "Tweets": len(data["tweets"]),
        "Engagement": data["engagement"],
    })

if summary:
    df = pd.DataFrame(summary)
    fig = px.bar(
        df, x="Tema", y="Tweets",
        color="Engagement",
        color_continuous_scale="Blues",
        text_auto=True,
    )
    fig.update_layout(xaxis_tickangle=-45, height=300)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Topic detail cards
for tid, terms in sorted_topics:
    data = topic_data.get(tid, {"tweets": [], "engagement": 0})
    topic_tweets = data["tweets"]
    topic_tweets.sort(key=lambda x: x.get("engagement", 0), reverse=True)

    count = len(topic_tweets)
    total_eng = data["engagement"]
    label = ", ".join(terms[:5])

    with st.expander(f"{label} ({count} posts, {total_eng:,} eng.)"):
        st.markdown(f"**Termos-chave:** {', '.join(terms[:10])}")
        st.markdown("**Posts representativos:**")

        for t in topic_tweets[:5]:
            render_tweet_card(t, compact=True)
