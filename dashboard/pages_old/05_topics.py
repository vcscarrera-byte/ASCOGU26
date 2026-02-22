"""Topic clustering visualization with clinical filters."""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates
from src.config import get_db_path
from src.db import create_tables, get_connection
from src.topic_model import cluster_and_summarize

st.set_page_config(page_title="Topics", layout="wide")
st.title("Topicos Mais Discutidos")

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

# Shared sidebar (no curated/limit for topics)
filters = render_sidebar_filters(conn, show_curated=False, show_limit=False)

with st.spinner("Clusterizando tweets..."):
    tweets, cluster_topics = cluster_and_summarize(
        conn,
        date=filters["date_filter"],
        selected_tumors=filters["selected_tumors"],
        selected_drugs=filters["selected_drugs"],
    )

conn.close()

if not tweets or not cluster_topics:
    st.info("Poucos tweets para clusterizacao com esses filtros.")
    st.stop()

# Summary bar chart
topic_counts = {}
topic_engagement = {}
for t in tweets:
    tid = t.get("topic_id", -1)
    if tid < 0:
        continue
    topic_counts[tid] = topic_counts.get(tid, 0) + 1
    topic_engagement[tid] = topic_engagement.get(tid, 0) + t.get("engagement", 0)

summary_data = []
for tid in sorted(cluster_topics.keys()):
    terms = ", ".join(cluster_topics[tid][:5])
    summary_data.append({
        "Topic": f"T{tid}: {terms}",
        "Tweets": topic_counts.get(tid, 0),
        "Engagement": topic_engagement.get(tid, 0),
    })

df_summary = pd.DataFrame(summary_data)

st.subheader("Distribuicao de Topicos")
fig = px.bar(
    df_summary, x="Topic", y="Tweets",
    color="Engagement",
    color_continuous_scale="Reds",
    text_auto=True,
)
fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# Topic detail cards
st.subheader("Detalhes por Topico")
for tid in sorted(cluster_topics.keys()):
    terms = cluster_topics[tid]
    topic_tweets = [t for t in tweets if t.get("topic_id") == tid]
    topic_tweets.sort(key=lambda x: x.get("engagement", 0), reverse=True)

    count = len(topic_tweets)
    total_eng = sum(t.get("engagement", 0) for t in topic_tweets)

    with st.expander(f"Topico {tid}: {', '.join(terms[:5])} ({count} tweets, {total_eng:,} eng.)"):
        st.markdown(f"**Top termos:** {', '.join(terms[:10])}")
        st.markdown("**Tweets representativos:**")

        for t in topic_tweets[:5]:
            tweet_url = f"https://x.com/{t['username']}/status/{t['tweet_id']}"
            st.markdown(
                f"- **@{t['username']}** ({t.get('engagement', 0)} eng.): "
                f"{t['text'][:200]}... [Ver no X]({tweet_url})"
            )
