"""Reusable UI components for the dashboard.

Design principles:
- Large, readable fonts (18px body via custom CSS)
- Content-first: posts visible, metrics secondary
- Clinical badges for quick scanning
"""

from datetime import datetime, timezone

import streamlit as st

from src.clinical_filters import classify_tweet_text

# ── Global CSS — typographic scale: 48 → 32 → 24 → 20 → 18 (min) ──
CUSTOM_CSS = """
<style>
    /* ── Title: 48px ── */
    [data-testid="stAppViewBlockContainer"] h1 {
        font-size: 48px !important;
        line-height: 1.15 !important;
        font-weight: 700 !important;
    }
    /* ── Subtitle / h2: 32px ── */
    [data-testid="stAppViewBlockContainer"] h2 {
        font-size: 32px !important;
        line-height: 1.25 !important;
        font-weight: 600 !important;
    }
    /* ── Section header / h3: 24px ── */
    [data-testid="stAppViewBlockContainer"] h3 {
        font-size: 24px !important;
        line-height: 1.3 !important;
        font-weight: 600 !important;
    }
    /* ── Body text: 20px ── */
    .stMarkdown p, .stMarkdown li {
        font-size: 20px !important;
        line-height: 1.6 !important;
    }
    /* Tweet text: 20px */
    .tweet-text p {
        font-size: 20px !important;
        line-height: 1.65 !important;
        color: #1a1a1a !important;
    }
    /* Abstract title: 20px */
    .abstract-title p {
        font-size: 20px !important;
        line-height: 1.55 !important;
        color: #1a1a1a !important;
    }
    /* Author header: 18px */
    .author-header p {
        font-size: 18px !important;
        font-weight: 500 !important;
    }
    /* Brief content: 18px */
    .brief-content p, .brief-content li {
        font-size: 18px !important;
        line-height: 1.6 !important;
    }
    /* ── Secondary / smallest: 18px ── */
    .tweet-metrics p {
        font-size: 18px !important;
        color: #555 !important;
    }
    .badge-row p {
        font-size: 18px !important;
    }
    .abstract-meta p {
        font-size: 18px !important;
        color: #555 !important;
    }
    .stats-bar p {
        font-size: 18px !important;
        color: #666 !important;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li {
        font-size: 18px !important;
    }
    /* Captions */
    .stCaption, [data-testid="stCaptionContainer"] p {
        font-size: 18px !important;
    }
    /* ── Links ── */
    a {
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    /* ── Metric labels & values ── */
    [data-testid="stMetricLabel"] p {
        font-size: 18px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
    }
    /* ── Card container ── */
    .card-container {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 12px;
        background: #fafbfc;
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

    st.markdown('<div class="card-container">', unsafe_allow_html=True)
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

    st.markdown('</div>', unsafe_allow_html=True)


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


# ── Session type badge colors ──
SESSION_BADGE = {
    "Oral Abstract Session": ":red-background[Oral]",
    "Rapid Oral Abstract Session": ":rainbow-background[Rapid Oral]",
    "General Session": ":violet-background[General]",
    "Poster Walks": ":blue-background[Poster Walk]",
    "Poster Session": ":gray-background[Poster]",
    "Trials in Progress Poster Session": ":gray-background[TIP]",
    "Networking Event": ":gray-background[Networking]",
}


def render_abstract_card(
    abstract: dict,
    rank: int | None = None,
    compact: bool = False,
    linked_tweet_count: int | None = None,
) -> None:
    """Render an abstract card with clinical badges and metadata."""
    abs_num = abstract.get("abstract_number", "")
    session_type = abstract.get("session_type", "")
    tumor = abstract.get("tumor_type", "")
    drugs_raw = abstract.get("drugs", "")
    buzz = linked_tweet_count if linked_tweet_count is not None else abstract.get("linked_tweet_count", 0)

    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    with st.container():
        # Header: number + session badge + buzz
        header_parts = []
        if rank:
            header_parts.append(f"**#{rank}**")
        header_parts.append(f"**#{abs_num}**")
        session_badge = SESSION_BADGE.get(session_type, f":gray-background[{session_type}]")
        header_parts.append(session_badge)
        if buzz:
            header_parts.append(f":violet-background[{buzz} tweets]")

        st.markdown(
            '<div class="author-header">\n\n' + " &nbsp; ".join(header_parts) + "\n\n</div>",
            unsafe_allow_html=True,
        )

        # Title
        title = abstract.get("title", "")
        display_title = title[:200] + "..." if len(title) > 200 else title
        st.markdown(
            f'<div class="abstract-title">\n\n**{display_title}**\n\n</div>',
            unsafe_allow_html=True,
        )

        # Presenter + tumor
        presenter = abstract.get("presenter", "")
        meta_parts = []
        if presenter:
            meta_parts.append(presenter)
        if tumor:
            meta_parts.append(tumor)
        if meta_parts:
            st.markdown(
                '<div class="abstract-meta">\n\n' + " · ".join(meta_parts) + "\n\n</div>",
                unsafe_allow_html=True,
            )

        # Clinical badges
        badges = []
        if tumor:
            badges.append(f":blue-background[{tumor}]")
        for d in drugs_raw.split("; "):
            d = d.strip()
            if d:
                badges.append(f":green-background[{d}]")
        if badges:
            st.markdown(
                '<div class="badge-row">\n\n' + " ".join(badges) + "\n\n</div>",
                unsafe_allow_html=True,
            )

        # Link to ASCO
        url = abstract.get("url", "")
        if url and not compact:
            st.markdown(f"[:link: **Ver no ASCO**]({url})")

    st.markdown('</div>', unsafe_allow_html=True)
