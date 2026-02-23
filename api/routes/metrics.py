"""Metrics endpoints."""

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/volume")
def get_volume(
    tumors: str | None = None,
    drugs: str | None = None,
):
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.aggregator import get_volume_by_day

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    selected_tumors = [t.strip() for t in tumors.split(",")] if tumors else None
    selected_drugs = [d.strip() for d in drugs.split(",")] if drugs else None

    data = get_volume_by_day(conn, selected_tumors=selected_tumors, selected_drugs=selected_drugs)
    conn.close()
    return {"data": data}
