"""Filter option endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def get_filter_options():
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.clinical_filters import get_tumor_type_names, get_drug_names

    tumors = get_tumor_type_names()
    drugs = get_drug_names()

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    try:
        from src.abstract_aggregator import get_session_type_names
        session_types = get_session_type_names(conn)
    except Exception:
        session_types = []

    conn.close()
    return {
        "tumors": tumors,
        "drugs": drugs,
        "session_types": session_types,
    }
