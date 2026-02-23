"""Daily brief endpoints."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/{date}")
def get_brief(date: str, lang: str = Query("pt")):
    from src.config import get_db_path
    from src.db import get_connection, create_tables, get_daily_brief

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)
    brief = get_daily_brief(conn, date, lang)
    conn.close()

    if not brief:
        return {"brief": None, "date": date, "language": lang}
    return {"brief": brief, "date": date, "language": lang}
