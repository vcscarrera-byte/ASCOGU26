"""FastAPI backend for ASCO GU RADAR dashboard."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import tweets, abstracts, authors, metrics, briefs, filters

app = FastAPI(title="ASCO GU RADAR API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tweets.router, prefix="/api/tweets", tags=["tweets"])
app.include_router(abstracts.router, prefix="/api/abstracts", tags=["abstracts"])
app.include_router(authors.router, prefix="/api/authors", tags=["authors"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(briefs.router, prefix="/api/briefs", tags=["briefs"])
app.include_router(filters.router, prefix="/api/filters", tags=["filters"])


@app.get("/api/stats")
def get_stats():
    """Quick stats: total tweets, authors, KOLs, abstracts."""
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.aggregator import get_quick_stats

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)

    stats = get_quick_stats(conn)
    try:
        abs_count = conn.execute("SELECT COUNT(*) FROM abstracts").fetchone()[0]
    except Exception:
        abs_count = 0
    stats["total_abstracts"] = abs_count
    conn.close()
    return stats


@app.get("/api/dates")
def get_dates():
    """Available dates with tweet data."""
    from src.config import get_db_path
    from src.db import get_connection, create_tables
    from src.aggregator import get_available_dates

    db_path = get_db_path()
    conn = get_connection(db_path)
    create_tables(conn)
    dates = get_available_dates(conn)
    conn.close()
    return {"dates": dates}
