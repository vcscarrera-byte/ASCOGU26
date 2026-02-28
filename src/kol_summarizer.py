"""Generate per-KOL daily summaries using Claude API."""

import logging
import sqlite3

import anthropic

from src.config import ANTHROPIC_API_KEY, get_summarizer_config
from src.db import save_kol_summary

logger = logging.getLogger(__name__)

PROMPT_EN = """You are a medical oncology conference analyst. Based on the following tweets \
from {name} (@{username}) at ASCO GU 2026 on {date}, write a concise summary.

{tweets_context}

Generate a summary with:
- 3-5 bullet points highlighting the key messages and clinical insights
- Include direct links to the relevant tweets
- Focus on clinical content, data, and expert opinions
- Use professional, scientific language

Format as markdown bullet points. Each bullet should reference the tweet link."""

PROMPT_PT = """Voce e um analista de congressos de oncologia medica. Com base nos seguintes tweets \
de {name} (@{username}) no ASCO GU 2026 em {date}, escreva um resumo conciso em portugues brasileiro.

{tweets_context}

Gere um resumo com:
- 3-5 bullet points destacando as mensagens-chave e insights clinicos
- Inclua links diretos para os tweets relevantes
- Foque em conteudo clinico, dados e opinioes de especialistas
- Use linguagem profissional e cientifica

Formate como bullet points em markdown. Cada bullet deve referenciar o link do tweet."""


def get_active_kols_for_date(
    conn: sqlite3.Connection, date: str, min_tweets: int = 2
) -> list[dict]:
    """Get curated KOLs with at least min_tweets original tweets on a given date."""
    rows = conn.execute(
        """SELECT u.user_id, u.username, u.name,
                  COUNT(t.tweet_id) as tweet_count
           FROM tweets t
           JOIN users u ON t.author_id = u.user_id
           WHERE u.is_curated = 1
             AND DATE(t.created_at) = ?
             AND t.text NOT LIKE 'RT @%%'
           GROUP BY u.user_id
           HAVING tweet_count >= ?
           ORDER BY tweet_count DESC""",
        (date, min_tweets),
    ).fetchall()
    return [dict(r) for r in rows]


def _get_kol_tweets(
    conn: sqlite3.Connection, user_id: str, date: str
) -> list[dict]:
    """Get all tweets from a KOL on a given date (excluding pure RTs)."""
    rows = conn.execute(
        """SELECT t.tweet_id, t.text, t.created_at,
                  t.like_count, t.retweet_count, t.reply_count, t.quote_count,
                  (t.like_count + t.retweet_count + t.reply_count + t.quote_count) as total_engagement,
                  u.username
           FROM tweets t
           JOIN users u ON t.author_id = u.user_id
           WHERE t.author_id = ?
             AND DATE(t.created_at) = ?
             AND t.text NOT LIKE 'RT @%%'
           ORDER BY total_engagement DESC""",
        (user_id, date),
    ).fetchall()
    return [dict(r) for r in rows]


def _build_tweets_context(tweets: list[dict]) -> str:
    """Build tweet context for the LLM prompt."""
    ctx = ""
    for i, tw in enumerate(tweets, 1):
        url = f"https://x.com/{tw['username']}/status/{tw['tweet_id']}"
        eng = tw["total_engagement"]
        text = tw["text"][:500].replace("\n", " ")
        ctx += f'\n{i}. ({eng} engagements): "{text}"\n   Link: {url}\n'
    return ctx


def generate_kol_summary(
    conn: sqlite3.Connection,
    user_id: str,
    username: str,
    name: str,
    date: str,
    lang: str = "en",
) -> str:
    """Generate a summary for a single KOL on a given date."""
    config = get_summarizer_config()

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    tweets = _get_kol_tweets(conn, user_id, date)
    if not tweets:
        return ""

    tweets_context = _build_tweets_context(tweets)
    prompt_template = PROMPT_PT if lang == "pt" else PROMPT_EN
    prompt = prompt_template.format(
        name=name, username=username, date=date, tweets_context=tweets_context
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config["model"],
        max_tokens=1024,
        temperature=config["temperature"],
        messages=[{"role": "user", "content": prompt}],
    )

    summary = message.content[0].text
    prompt_tokens = message.usage.input_tokens
    completion_tokens = message.usage.output_tokens

    save_kol_summary(
        conn, user_id, date, lang, summary,
        tweet_count=len(tweets),
        model_used=config["model"],
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    return summary


def generate_all_kol_summaries(
    conn: sqlite3.Connection, date: str, min_tweets: int = 2
) -> dict:
    """Generate EN+PT summaries for all active KOLs on a date.

    Returns stats dict.
    """
    kols = get_active_kols_for_date(conn, date, min_tweets)
    logger.info(f"Found {len(kols)} active KOLs for {date} (min_tweets={min_tweets})")

    generated = 0
    for kol in kols:
        username = kol["username"]
        name = kol["name"]
        user_id = kol["user_id"]
        tweet_count = kol["tweet_count"]

        logger.info(f"  Generating summaries for @{username} ({tweet_count} tweets)...")

        for lang in ("en", "pt"):
            try:
                generate_kol_summary(conn, user_id, username, name, date, lang)
                generated += 1
            except Exception as exc:
                logger.error(f"  Failed for @{username} ({lang}): {exc}")

    return {
        "date": date,
        "kols_found": len(kols),
        "summaries_generated": generated,
    }
