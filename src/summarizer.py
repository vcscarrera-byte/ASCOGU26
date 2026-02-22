"""Generate daily briefs using Claude API."""

import logging
import sqlite3
from pathlib import Path

import anthropic

from src.aggregator import get_top_tweets, get_volume_by_day
from src.config import ANTHROPIC_API_KEY, get_briefs_dir, get_summarizer_config
from src.db import save_daily_brief
from src.topic_model import cluster_and_summarize

logger = logging.getLogger(__name__)

PROMPT_EN = """You are a medical oncology conference analyst. Based on the following Twitter/X data \
from ASCO GU 2026 (Genitourinary Cancers Symposium) on {date}, generate a daily brief.

{context}

Generate a brief with these sections:

## What Blew Up Today
Identify the 3-5 highest-engagement posts and explain WHY they got attention.
Include the direct link to each tweet.

## Main Themes
Based on the topic clusters and top tweets, identify 3-5 main discussion themes.
For each theme, provide 1-2 representative tweet links.

## Key Takeaways and Opinions
Summarize the most notable clinical data points, expert opinions, or controversies.
For EACH point, include the source tweet link for auditability.

## By the Numbers
Quick stats: total tweets, top author, most-engaged post, etc.

IMPORTANT: Every claim must have a tweet link. Do not fabricate or hallucinate content.
Only summarize what is actually in the provided data."""

PROMPT_PT = """Voce e um analista de congressos de oncologia medica. Com base nos seguintes dados do Twitter/X \
do ASCO GU 2026 (Simposio de Canceres Genitourinarios) em {date}, gere um resumo diario em portugues brasileiro.

{context}

Gere um resumo com estas secoes:

## O Que Bombou Hoje
Identifique os 3-5 posts com maior engajamento e explique POR QUE chamaram atencao.
Inclua o link direto para cada tweet.

## Principais Temas
Com base nos clusters de topicos e top tweets, identifique 3-5 temas principais de discussao.
Para cada tema, inclua 1-2 links de tweets representativos.

## Pontos-Chave e Opinioes
Resuma os dados clinicos mais notaveis, opinioes de especialistas ou controversias.
Para CADA ponto, inclua o link do tweet fonte para auditabilidade.

## Numeros do Dia
Estatisticas rapidas: total de tweets, top autor, post mais engajado, etc.

IMPORTANTE: Cada afirmacao deve ter um link de tweet. Nao fabrique ou alucine conteudo.
Resuma apenas o que esta nos dados fornecidos."""


def _build_context(
    conn: sqlite3.Connection,
    date: str,
    top_tweets: list[dict],
    cluster_topics: dict[int, list[str]],
) -> str:
    """Build the context document for the LLM prompt."""
    # Get daily volume
    volume = get_volume_by_day(conn)
    day_data = next((v for v in volume if v["date"] == date), None)

    ctx = f"## Daily Tweet Collection for {date}\n\n### Metrics\n"
    if day_data:
        ctx += f"- Total tweets: {day_data['tweets']}\n"
        ctx += f"- Unique authors: {day_data['authors']}\n"
        ctx += f"- Total engagement: {day_data['engagement']}\n"
        ctx += f"- Likes: {day_data['likes']}, Retweets: {day_data['retweets']}, "
        ctx += f"Replies: {day_data['replies']}, Quotes: {day_data['quotes']}\n"

    ctx += "\n### Top 15 Tweets by Engagement\n"
    for i, tweet in enumerate(top_tweets[:15], 1):
        eng = tweet["total_engagement"]
        url = f"https://x.com/{tweet['username']}/status/{tweet['tweet_id']}"
        text = tweet["text"][:300].replace("\n", " ")
        ctx += f"\n{i}. @{tweet['username']} ({eng} engagements):\n"
        ctx += f'   "{text}"\n'
        ctx += f"   Link: {url}\n"

    ctx += "\n### Topic Clusters\n"
    for cid, terms in cluster_topics.items():
        ctx += f"- Cluster {cid}: {', '.join(terms[:5])}\n"

    return ctx


def generate_brief(
    conn: sqlite3.Connection,
    date: str,
    language: str = "en",
) -> str:
    """Generate a daily brief for a given date and language.

    Args:
        conn: SQLite connection
        date: YYYY-MM-DD
        language: "en" or "pt"

    Returns:
        Generated brief markdown
    """
    config = get_summarizer_config()

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set. Check your .env file.")

    # Gather data
    top_tweets = get_top_tweets(conn, date=date, limit=15)
    if not top_tweets:
        return f"# No data for {date}\n\nNo tweets collected for this date."

    tweets_with_topics, cluster_topics = cluster_and_summarize(conn, date)

    context = _build_context(conn, date, top_tweets, cluster_topics)

    prompt_template = PROMPT_PT if language == "pt" else PROMPT_EN
    prompt = prompt_template.format(date=date, context=context)

    logger.info(f"Generating {language.upper()} brief for {date} using {config['model']}")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=config["model"],
        max_tokens=config["max_tokens"],
        temperature=config["temperature"],
        messages=[{"role": "user", "content": prompt}],
    )

    brief_text = message.content[0].text
    prompt_tokens = message.usage.input_tokens
    completion_tokens = message.usage.output_tokens

    # Save to DB
    save_daily_brief(conn, date, language, brief_text, config["model"],
                     prompt_tokens, completion_tokens)

    # Save to file
    briefs_dir = get_briefs_dir()
    suffix = "pt" if language == "pt" else "en"
    brief_path = briefs_dir / f"{date}_{suffix}.md"
    brief_path.write_text(brief_text, encoding="utf-8")
    logger.info(f"Brief saved to {brief_path}")

    return brief_text


def generate_both_briefs(conn: sqlite3.Connection, date: str) -> dict[str, str]:
    """Generate briefs in both EN and PT-BR."""
    results = {}
    for lang in ("en", "pt"):
        results[lang] = generate_brief(conn, date, lang)
    return results
