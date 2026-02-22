"""Query functions for abstracts — parallel to aggregator.py for tweets."""

import sqlite3

from src.clinical_filters import get_clinical_filter_config


def _get_drug_synonyms(drug_name: str) -> list[str]:
    """Get all synonyms for a drug from config."""
    cfg = get_clinical_filter_config()
    drugs = cfg.get("drugs", {})
    # Try exact match first
    if drug_name in drugs:
        return drugs[drug_name]
    # Try case-insensitive match
    for key, synonyms in drugs.items():
        if key.lower() == drug_name.lower():
            return synonyms
    # Fallback: just the name itself
    return [drug_name]


def _build_abstract_where(
    conditions: list[str],
    params: list,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
    session_types: list[str] | None = None,
    text_search: str | None = None,
) -> None:
    """Append filter conditions for abstract queries (mutates in-place)."""
    # Tumor: exact match on pre-computed tumor_type column
    if selected_tumors:
        placeholders = ",".join("?" * len(selected_tumors))
        conditions.append(f"a.tumor_type IN ({placeholders})")
        params.extend(selected_tumors)

    # Drugs: LIKE on semicolon-separated drugs column (with synonyms)
    if selected_drugs:
        drug_or_parts = []
        for drug_name in selected_drugs:
            synonyms = _get_drug_synonyms(drug_name)
            for syn in synonyms:
                drug_or_parts.append("LOWER(a.drugs) LIKE ?")
                params.append(f"%{syn.lower()}%")
        if drug_or_parts:
            conditions.append(f"({' OR '.join(drug_or_parts)})")

    # Session type: exact match
    if session_types:
        placeholders = ",".join("?" * len(session_types))
        conditions.append(f"a.session_type IN ({placeholders})")
        params.extend(session_types)

    # Text search: LIKE on title + body
    if text_search and text_search.strip():
        search_term = f"%{text_search.strip().lower()}%"
        conditions.append("(LOWER(a.title) LIKE ? OR LOWER(a.body) LIKE ?)")
        params.extend([search_term, search_term])


def get_all_abstracts(
    conn: sqlite3.Connection,
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
    session_types: list[str] | None = None,
    text_search: str | None = None,
    sort_by: str = "session_rank",
    limit: int = 100,
) -> list[dict]:
    """Browse abstracts with filtering and sorting."""
    query = """
        SELECT a.*,
               COALESCE(lc.tweet_count, 0) as linked_tweet_count
        FROM abstracts a
        LEFT JOIN (
            SELECT abstract_number, COUNT(*) as tweet_count
            FROM tweet_abstract_links
            GROUP BY abstract_number
        ) lc ON a.abstract_number = lc.abstract_number
    """
    conditions: list[str] = []
    params: list = []
    _build_abstract_where(conditions, params, selected_tumors, selected_drugs, session_types, text_search)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Sort
    sort_clauses = {
        "session_rank": "a.session_rank DESC, a.abstract_number ASC",
        "buzz": "linked_tweet_count DESC, a.session_rank DESC",
        "number": "a.abstract_number ASC",
        "relevance": "a.session_rank DESC, linked_tweet_count DESC",
    }
    query += f" ORDER BY {sort_clauses.get(sort_by, sort_clauses['session_rank'])}"
    query += " LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_abstract_detail(
    conn: sqlite3.Connection, abstract_number: str
) -> dict | None:
    """Get a single abstract with linked tweet count."""
    row = conn.execute(
        """SELECT a.*,
                  COALESCE(lc.tweet_count, 0) as linked_tweet_count
           FROM abstracts a
           LEFT JOIN (
               SELECT abstract_number, COUNT(*) as tweet_count
               FROM tweet_abstract_links
               GROUP BY abstract_number
           ) lc ON a.abstract_number = lc.abstract_number
           WHERE a.abstract_number = ?""",
        (abstract_number,),
    ).fetchone()
    return dict(row) if row else None


def get_abstract_stats(conn: sqlite3.Connection) -> dict:
    """Summary stats: total, by session type, by tumor, top drugs."""
    total = conn.execute("SELECT COUNT(*) FROM abstracts").fetchone()[0]

    # By session type
    session_rows = conn.execute(
        """SELECT session_type, COUNT(*) as cnt
           FROM abstracts WHERE session_type != ''
           GROUP BY session_type ORDER BY cnt DESC"""
    ).fetchall()
    by_session = {r["session_type"]: r["cnt"] for r in session_rows}

    # By tumor type
    tumor_rows = conn.execute(
        """SELECT tumor_type, COUNT(*) as cnt
           FROM abstracts WHERE tumor_type != ''
           GROUP BY tumor_type ORDER BY cnt DESC"""
    ).fetchall()
    by_tumor = {r["tumor_type"]: r["cnt"] for r in tumor_rows}

    # Top drugs (split semicolon-separated field)
    drug_rows = conn.execute(
        "SELECT drugs FROM abstracts WHERE drugs != ''"
    ).fetchall()
    drug_counts: dict[str, int] = {}
    for r in drug_rows:
        for d in r["drugs"].split("; "):
            d = d.strip()
            if d:
                drug_counts[d] = drug_counts.get(d, 0) + 1
    top_drugs = dict(sorted(drug_counts.items(), key=lambda x: -x[1])[:20])

    # With buzz
    buzz_count = conn.execute(
        """SELECT COUNT(DISTINCT abstract_number) FROM tweet_abstract_links"""
    ).fetchone()[0]

    return {
        "total": total,
        "by_session_type": by_session,
        "by_tumor": by_tumor,
        "top_drugs": top_drugs,
        "with_buzz": buzz_count,
    }


def get_abstracts_with_buzz(
    conn: sqlite3.Connection, min_tweets: int = 1, limit: int = 20,
) -> list[dict]:
    """Get abstracts sorted by linked tweet count (buzz)."""
    rows = conn.execute(
        """SELECT a.*, COUNT(tal.tweet_id) as linked_tweet_count
           FROM abstracts a
           JOIN tweet_abstract_links tal ON a.abstract_number = tal.abstract_number
           GROUP BY a.abstract_number
           HAVING linked_tweet_count >= ?
           ORDER BY linked_tweet_count DESC, a.session_rank DESC
           LIMIT ?""",
        (min_tweets, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def get_session_type_names(conn: sqlite3.Connection) -> list[str]:
    """Get distinct session types from abstracts table."""
    rows = conn.execute(
        """SELECT DISTINCT session_type FROM abstracts
           WHERE session_type != '' ORDER BY session_type"""
    ).fetchall()
    return [r["session_type"] for r in rows]


def get_abstract_drug_names(conn: sqlite3.Connection) -> list[str]:
    """Get distinct drugs from the abstracts table."""
    rows = conn.execute(
        "SELECT drugs FROM abstracts WHERE drugs != ''"
    ).fetchall()
    drugs: set[str] = set()
    for r in rows:
        for d in r["drugs"].split("; "):
            d = d.strip()
            if d:
                drugs.add(d)
    return sorted(drugs)
