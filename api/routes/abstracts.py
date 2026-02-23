"""Abstract endpoints."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/stats")
def get_abstract_stats():
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.abstract_aggregator import get_abstract_stats as _get_stats

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)
    stats = _get_stats(conn)
    conn.close()
    return stats


@router.get("/buzz")
def get_buzz_abstracts(limit: int = Query(10, ge=1, le=50)):
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.abstract_aggregator import get_abstracts_with_buzz

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)
    abstracts = get_abstracts_with_buzz(conn, min_tweets=1, limit=limit)
    conn.close()
    return {"abstracts": abstracts}


@router.get("/{abstract_number}")
def get_abstract_detail(abstract_number: str):
    from src.config import get_db_path
    from src.db import get_connection, create_tables, get_linked_tweets
    from src.abstract_aggregator import get_abstract_detail as _get_detail

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)
    detail = _get_detail(conn, abstract_number)
    linked_tweets = get_linked_tweets(conn, abstract_number) if detail else []
    conn.close()

    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Abstract not found")

    return {"abstract": detail, "linked_tweets": linked_tweets}


@router.get("")
def get_all_abstracts(
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=100),
    tumors: str | None = None,
    drugs: str | None = None,
    sessions: str | None = None,
    search: str | None = None,
    sort: str = Query("session_rank", pattern="^(session_rank|buzz|number)$"),
):
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.abstract_aggregator import get_all_abstracts as _get_all

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    selected_tumors = [t.strip() for t in tumors.split(",")] if tumors else None
    selected_drugs = [d.strip() for d in drugs.split(",")] if drugs else None
    session_types = [s.strip() for s in sessions.split(",")] if sessions else None

    abstracts = _get_all(conn, selected_tumors=selected_tumors, selected_drugs=selected_drugs,
                         session_types=session_types, text_search=search,
                         sort_by=sort, limit=size)
    conn.close()
    return {"abstracts": abstracts, "total": len(abstracts)}
