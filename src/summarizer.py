"""Generate daily briefs using Claude API."""

import logging
import sqlite3
from pathlib import Path

import anthropic

from src.aggregator import get_top_tweets, get_volume_by_day
from src.config import ANTHROPIC_API_KEY, get_briefs_dir, get_summarizer_config
from src.db import save_daily_brief
from src.topic_model import cluster_and_summarize

try:
    from src.abstract_aggregator import get_abstracts_with_buzz, get_all_abstracts
except ImportError:
    get_abstracts_with_buzz = None
    get_all_abstracts = None

logger = logging.getLogger(__name__)

PROMPT_EN = """You are a medical oncology conference analyst, writing for urologists and oncologists. \
Based on the following Twitter/X data and abstracts from ASCO GU 2026 (Genitourinary Cancers Symposium) on {date}, \
generate a professional daily brief.

{context}

Generate a brief with these sections:

# Daily Brief — ASCO GU 2026 | {date}

## Today's Highlights
Identify the 3-5 highest-engagement posts and explain WHY they got attention from the medical community.
Include the direct link to each tweet. Focus on clinical content, not engagement metrics.

## Key Discussion Themes
Based on the topic clusters, tweets, and related abstracts, identify 3-5 main discussion themes.
For each theme, provide 1-2 representative tweet links.
If abstracts are related, mention the abstract number and relevant PICO data \
(Population, Intervention, Comparator, Outcome).

## Clinical Evidence and Expert Opinions
Summarize the most notable clinical data points, expert opinions, or controversies.
For EACH point, include the source tweet link. When referencing study data, \
cite the corresponding abstract if available.

## By the Numbers
Quick stats: total tweets, top author, most-engaged post, etc.

IMPORTANT: Every claim must have a tweet link or abstract reference. Do not fabricate or hallucinate content.
Only summarize what is actually in the provided data. Maintain professional, scientific tone throughout.
Do NOT use informal expressions such as "blew up", "went viral", "buzz", "hot takes" etc. Use formal academic language."""

PROMPT_PT = """Voce e um analista de congressos de oncologia medica, escrevendo para urologistas e oncologistas. \
Com base nos seguintes dados do Twitter/X e abstracts do ASCO GU 2026 (Simposio de Canceres Genitourinarios) em {date}, \
gere um resumo diario em portugues brasileiro. Use tom profissional e tecnico, adequado para medicos especialistas.

{context}

Gere um resumo com estas secoes:

# Resumo Diario — ASCO GU 2026 | {date}

## Destaques do Dia
Identifique os 3-5 posts com maior engajamento e explique POR QUE chamaram atencao da comunidade medica.
Inclua o link direto para cada tweet. Foque no conteudo clinico, nao em metricas de engajamento.

## Principais Temas em Discussao
Com base nos clusters de topicos, tweets e abstracts relacionados, identifique 3-5 temas principais.
Para cada tema, inclua links de tweets representativos.
Se houver abstracts relacionados ao tema, mencione o numero do abstract e os dados PICO relevantes \
(Populacao, Intervencao, Comparador, Desfecho).

## Evidencias Clinicas e Opinioes de Especialistas
Resuma os dados clinicos mais notaveis, opinioes de especialistas ou controversias.
Para CADA ponto, inclua o link do tweet fonte. Quando mencionar dados de estudos, \
referencie o abstract correspondente se disponivel.

## Numeros do Dia
Estatisticas rapidas: total de tweets, top autor, post mais engajado, etc.

IMPORTANTE: Cada afirmacao deve ter um link de tweet ou referencia a abstract. Nao fabrique ou alucine conteudo.
Resuma apenas o que esta nos dados fornecidos. Mantenha tom profissional e cientifico — \
evite girias ou expressoes coloquiais como "bombou", "viralizou" etc."""


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

    # Add abstract context if available
    ctx += _build_abstract_context(conn)

    return ctx


def _build_abstract_context(conn: sqlite3.Connection) -> str:
    """Add relevant abstracts to the context for richer summaries."""
    ctx = ""

    # Abstracts with buzz (mentioned in tweets)
    if get_abstracts_with_buzz:
        try:
            buzz = get_abstracts_with_buzz(conn, min_tweets=1, limit=10)
            if buzz:
                ctx += "\n### Abstracts Discussed in Tweets\n"
                for a in buzz:
                    num = a.get("abstract_number", "?")
                    title = a.get("title", "")[:200]
                    session = a.get("session_type", "")
                    tumor = a.get("tumor_type", "")
                    drugs = a.get("drugs", "")
                    tweet_count = a.get("linked_tweet_count", 0)
                    ctx += f"\n- Abstract #{num} ({session}): {title}\n"
                    if tumor:
                        ctx += f"  Population: {tumor}\n"
                    if drugs:
                        ctx += f"  Intervention/Drugs: {drugs}\n"
                    ctx += f"  Referenced in {tweet_count} tweets\n"
        except Exception:
            pass

    # Top oral abstracts (most important presentations)
    if get_all_abstracts:
        try:
            orals = get_all_abstracts(
                conn,
                session_types=["Oral Abstract Session", "Rapid Oral Abstract Session"],
                sort_by="session_rank",
                limit=10,
            )
            if orals:
                ctx += "\n### Key Oral Presentations\n"
                for a in orals:
                    num = a.get("abstract_number", "?")
                    title = a.get("title", "")[:200]
                    session = a.get("session_type", "")
                    tumor = a.get("tumor_type", "")
                    drugs = a.get("drugs", "")
                    presenter = a.get("presenter", "")
                    body = a.get("body", "")
                    ctx += f"\n- Abstract #{num} ({session}): {title}\n"
                    if presenter:
                        ctx += f"  Presenter: {presenter}\n"
                    if tumor:
                        ctx += f"  Population: {tumor}\n"
                    if drugs:
                        ctx += f"  Intervention/Drugs: {drugs}\n"
                    if body and "full, final text" not in body.lower() and len(body) > 50:
                        ctx += f"  Summary: {body[:500]}\n"
        except Exception:
            pass

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
