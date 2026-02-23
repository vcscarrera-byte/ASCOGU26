"""Author endpoints."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("")
def get_authors(
    limit: int = Query(20, ge=1, le=100),
    tumors: str | None = None,
    drugs: str | None = None,
    curated: bool = False,
):
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.aggregator import get_top_authors

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    selected_tumors = [t.strip() for t in tumors.split(",")] if tumors else None
    selected_drugs = [d.strip() for d in drugs.split(",")] if drugs else None

    authors = get_top_authors(conn, limit=limit, selected_tumors=selected_tumors, selected_drugs=selected_drugs)
    if curated:
        authors = [a for a in authors if a.get("is_curated")]
    conn.close()
    return {"authors": authors, "total": len(authors)}
