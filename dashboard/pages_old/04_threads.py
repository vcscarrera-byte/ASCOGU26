"""Top threads by conversation_id with clinical badges."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from dashboard.sidebar_filters import render_sidebar_filters
from src.aggregator import get_available_dates, get_thread_tweets, get_top_threads
from src.clinical_filters import classify_tweet_text
from src.config import get_db_path
from src.db import create_tables, get_connection

st.set_page_config(page_title="Top Threads", layout="wide")
st.title("Top Threads")

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
filters = render_sidebar_filters(conn, show_curated=False, max_limit=30, default_limit=15)

threads = get_top_threads(
    conn,
    date=filters["date_filter"],
    limit=filters["limit"],
    selected_tumors=filters["selected_tumors"],
    selected_drugs=filters["selected_drugs"],
)

if not threads:
    st.info("Nenhuma thread encontrada com esses filtros.")
    conn.close()
    st.stop()

for i, thread in enumerate(threads, 1):
    cid = thread["conversation_id"]
    eng = thread["total_engagement"]
    size = thread["thread_size"]

    with st.expander(f"#{i} - Thread ({size} tweets, {eng:,} engagement) - {thread['started_at'][:16]}"):
        thread_tweets = get_thread_tweets(conn, cid)
        for t in thread_tweets:
            tweet_url = f"https://x.com/{t['username']}/status/{t['tweet_id']}"
            classification = classify_tweet_text(t["text"])

            st.markdown(f"**{t['name']}** (@{t['username']}) - {t['created_at'][:16]}")

            # Clinical badges
            badges = []
            for tumor in classification["tumor_types"]:
                badges.append(f":blue[{tumor}]")
            for drug in classification["drugs"]:
                badges.append(f":green[{drug}]")
            if badges:
                st.markdown(" ".join(badges))

            st.markdown(t["text"])
            st.caption(
                f"Likes: {t['like_count']} | RTs: {t['retweet_count']} | "
                f"Replies: {t['reply_count']} | Quotes: {t['quote_count']} | "
                f"[Ver no X]({tweet_url})"
            )
            st.markdown("---")

conn.close()
