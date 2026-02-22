"""Top posts by engagement with clinical badges."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates, get_top_tweets
from src.clinical_filters import classify_tweet_text
from src.config import get_db_path
from src.db import create_tables, get_connection

st.set_page_config(page_title="Top Posts", layout="wide")
st.title("Top Posts por Engajamento")

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

# Shared sidebar with all filters
filters = render_sidebar_filters(conn)

tweets = get_top_tweets(
    conn,
    date=filters["date_filter"],
    limit=filters["limit"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
)
conn.close()

if filters["curated_only"]:
    tweets = [t for t in tweets if t["is_curated"]]

if not tweets:
    st.info("Nenhum tweet encontrado com esses filtros.")
    st.stop()

for i, t in enumerate(tweets, 1):
    eng = t["total_engagement"]
    tweet_url = f"https://x.com/{t['username']}/status/{t['tweet_id']}"
    classification = classify_tweet_text(t["text"])

    with st.container():
        col1, col2 = st.columns([1, 12])
        with col1:
            st.markdown(f"**#{i}**")
        with col2:
            # Author line with curated badge
            curated_badge = " :star:" if t["is_curated"] else ""
            st.markdown(f"**{t['name']}** (@{t['username']}){curated_badge}")

            # Clinical badges
            badges = []
            for tumor in classification["tumor_types"]:
                badges.append(f":blue[{tumor}]")
            for drug in classification["drugs"]:
                badges.append(f":green[{drug}]")
            if badges:
                st.markdown(" ".join(badges))

            # Full tweet text
            st.markdown(t["text"])

            # Engagement metrics
            mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
            mcol1.metric("Likes", f"{t['like_count']:,}")
            mcol2.metric("RTs", f"{t['retweet_count']:,}")
            mcol3.metric("Replies", f"{t['reply_count']:,}")
            mcol4.metric("Quotes", f"{t['quote_count']:,}")
            mcol5.metric("Total", f"{eng:,}")

            # Link to X + timestamp
            st.markdown(
                f":link: [Ver no X]({tweet_url}) | {t['created_at'][:16]}"
            )
        st.divider()
