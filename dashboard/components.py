"""Reusable UI components for the dashboard.

Design principles:
- Large, readable fonts (18px body via custom CSS)
- Content-first: posts visible, metrics secondary
- Clinical badges for quick scanning
"""

from datetime import datetime, timezone

import streamlit as st

from src.clinical_filters import classify_tweet_text

# ── Global CSS for readability ──
CUSTOM_CSS = """
<style>
    /* Larger base font */
    .stMarkdown p, .stMarkdown li {
        font-size: 1.12rem !important;
        line-height: 1.65 !important;
    }
    /* Tweet text even larger */
    .tweet-text p {
        font-size: 1.18rem !important;
        line-height: 1.7 !important;
        color: #1a1a1a !important;
    }
    /* Author header */
    .author-header p {
        font-size: 1.05rem !important;
        font-weight: 500 !important;
    }
    /* Metrics smaller but still readable */
    .tweet-metrics p {
        font-size: 0.95rem !important;
        color: #555 !important;
    }
    /* Badge styling */
    .badge-row p {
        font-size: 0.95rem !important;
    }
    /* Sidebar text slightly smaller */
    section[data-testid="stSidebar"] .stMarkdown p {
        font-size: 0.95rem !important;
    }
    /* Brief sections */
    .brief-content p, .brief-content li {
        font-size: 1.1rem !important;
        line-height: 1.65 !important;
    }
    /* Better link styling */
    a {
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    /* Stats bar */
    .stats-bar p {
        font-size: 1.0rem !important;
        color: #666 !important;
    }
</style>
"""


def inject_custom_css() -> None:
    """Inject custom CSS for readability. Call once per page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def _relative_time(created_at: str) -> str:
    """Convert ISO timestamp to relative time string."""
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        minutes = int(diff.total_seconds() / 60)
        if minutes < 60:
            return f"{minutes}min"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h"
        days = hours // 24
        if days == 1:
            return "ontem"
        return f"{days}d"
    except (ValueError, TypeError):
        return created_at[:16] if created_at else ""


def _format_number(n: int) -> str:
    """Format number: 1200 -> 1.2K, 50 -> 50."""
    if n is None:
        return "0"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def render_tweet_card(
    tweet: dict,
    rank: int | None = None,
    compact: bool = False,
    show_relevance: bool = False,
) -> None:
    """Render a tweet card with clinical badges and actions."""
    tweet_url = f"https://x.com/{tweet.get('username', '')}/status/{tweet.get('tweet_id', '')}"
    clinical = tweet.get("clinical_tags") or classify_tweet_text(tweet.get("text", ""))

    with st.container():
        # Header: author + time
        curated = " :star:" if tweet.get("is_curated") else ""
        name = tweet.get("name", "")
        username = tweet.get("username", "")
        time_ago = _relative_time(tweet.get("created_at", ""))

        header_parts = []
        if rank:
            header_parts.append(f"**#{rank}**")
        header_parts.append(f"**{name}** (@{username}){curated}")
        if time_ago:
            header_parts.append(f"*{time_ago}*")

        st.markdown(
            '<div class="author-header">\n\n' + " · ".join(header_parts) + "\n\n</div>",
            unsafe_allow_html=True,
        )

        # Clinical badges
        badges = []
        for tumor in clinical.get("tumor_types", []):
            badges.append(f":blue-background[{tumor}]")
        for drug in clinical.get("drugs", []):
            badges.append(f":green-background[{drug}]")
        if show_relevance and "relevance_score" in tweet:
            score = tweet["relevance_score"]
            if score >= 60:
                badges.insert(0, f":red-background[{score}]")
            elif score >= 30:
                badges.insert(0, f":orange-background[{score}]")
        if badges:
            st.markdown(
                '<div class="badge-row">\n\n' + " ".join(badges) + "\n\n</div>",
                unsafe_allow_html=True,
            )

        # Tweet text (large, readable)
        text = tweet.get("text", "")
        is_rt = text.startswith("RT @")
        if is_rt:
            st.markdown(
                f'<div class="tweet-text">\n\n*{text}*\n\n</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="tweet-text">\n\n{text}\n\n</div>',
                unsafe_allow_html=True,
            )

        # Metrics + link
        likes = _format_number(tweet.get("like_count", 0))
        rts = _format_number(tweet.get("retweet_count", 0))
        replies = _format_number(tweet.get("reply_count", 0))
        impressions = _format_number(tweet.get("impression_count", 0))

        if not compact:
            st.markdown(
                f'<div class="tweet-metrics">\n\n'
                f":heart: {likes}  &nbsp; :repeat: {rts}  &nbsp; "
                f":speech_balloon: {replies}  &nbsp; :eyes: {impressions}  &nbsp;&nbsp; "
                f"[:link: **Ver no X**]({tweet_url})"
                f"\n\n</div>",
                unsafe_allow_html=True,
            )
        else:
            eng = (
                tweet.get("like_count", 0)
                + tweet.get("retweet_count", 0)
                + tweet.get("reply_count", 0)
                + tweet.get("quote_count", 0)
            )
            st.markdown(
                f'<div class="tweet-metrics">\n\n'
                f":heart: {likes} · :repeat: {rts} · :speech_balloon: {replies} · "
                f"Total: {_format_number(eng)} · "
                f"[:link: Ver no X]({tweet_url})"
                f"\n\n</div>",
                unsafe_allow_html=True,
            )

        st.divider()


def render_brief_section(brief_markdown: str) -> None:
    """Render the daily brief as structured sections (no expanders — safe to nest)."""
    if not brief_markdown:
        st.info("Nenhum brief disponivel para esta data.")
        return

    sections = []
    current_title = ""
    current_body = []

    for line in brief_markdown.split("\n"):
        if line.startswith("## "):
            if current_title:
                sections.append((current_title, "\n".join(current_body)))
            current_title = line[3:].strip()
            current_body = []
        elif line.startswith("# "):
            st.markdown(line)
        else:
            current_body.append(line)

    if current_title:
        sections.append((current_title, "\n".join(current_body)))

    for title, body in sections:
        st.markdown(f"**{title}**")
        st.markdown(
            f'<div class="brief-content">\n\n{body.strip()}\n\n</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")


def render_mini_stats(
    total_tweets: int,
    unique_authors: int,
    total_engagement: int,
    curated_active: int = 0,
) -> None:
    """Render a single-line stats bar (subtle, not dominating)."""
    parts = [
        f"**{total_tweets}** tweets",
        f"**{unique_authors}** autores",
        f"**{_format_number(total_engagement)}** engajamentos",
    ]
    if curated_active:
        parts.append(f"**{curated_active}** KOLs ativos")
    st.markdown(
        '<div class="stats-bar">\n\n' + " · ".join(parts) + "\n\n</div>",
        unsafe_allow_html=True,
    )
