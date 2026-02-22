"""SQLite database: schema creation, insert/upsert helpers."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with WAL mode and return it."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS collection_runs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at      TEXT NOT NULL,
            finished_at     TEXT,
            query_hash      TEXT NOT NULL,
            start_time      TEXT NOT NULL,
            end_time        TEXT NOT NULL,
            tweets_fetched  INTEGER DEFAULT 0,
            tweets_new      INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'running',
            error_message   TEXT
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id             TEXT PRIMARY KEY,
            name                TEXT,
            username            TEXT NOT NULL,
            description         TEXT,
            profile_image_url   TEXT,
            verified            INTEGER DEFAULT 0,
            followers_count     INTEGER DEFAULT 0,
            following_count     INTEGER DEFAULT 0,
            tweet_count         INTEGER DEFAULT 0,
            listed_count        INTEGER DEFAULT 0,
            is_curated          INTEGER DEFAULT 0,
            first_seen_at       TEXT NOT NULL,
            last_updated_at     TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_is_curated ON users(is_curated);

        CREATE TABLE IF NOT EXISTS tweets (
            tweet_id            TEXT PRIMARY KEY,
            author_id           TEXT NOT NULL,
            text                TEXT NOT NULL,
            created_at          TEXT NOT NULL,
            conversation_id     TEXT,
            in_reply_to_user_id TEXT,
            lang                TEXT,
            source              TEXT,
            retweet_count       INTEGER DEFAULT 0,
            reply_count         INTEGER DEFAULT 0,
            like_count          INTEGER DEFAULT 0,
            quote_count         INTEGER DEFAULT 0,
            impression_count    INTEGER DEFAULT 0,
            bookmark_count      INTEGER DEFAULT 0,
            referenced_tweets   TEXT,
            entities            TEXT,
            context_annotations TEXT,
            collection_run_id   INTEGER,
            collected_at        TEXT NOT NULL,
            FOREIGN KEY (author_id) REFERENCES users(user_id),
            FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id)
        );
        CREATE INDEX IF NOT EXISTS idx_tweets_author_id ON tweets(author_id);
        CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at);
        CREATE INDEX IF NOT EXISTS idx_tweets_conversation_id ON tweets(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_tweets_collection_run ON tweets(collection_run_id);

        CREATE TABLE IF NOT EXISTS daily_metrics (
            date                TEXT NOT NULL,
            metric_name         TEXT NOT NULL,
            metric_value        REAL NOT NULL,
            breakdown_key       TEXT DEFAULT '',
            breakdown_value     TEXT DEFAULT '',
            computed_at         TEXT NOT NULL,
            PRIMARY KEY (date, metric_name, breakdown_key, breakdown_value)
        );
        CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);

        CREATE TABLE IF NOT EXISTS daily_briefs (
            date                TEXT NOT NULL,
            language            TEXT NOT NULL DEFAULT 'en',
            brief_markdown      TEXT NOT NULL,
            model_used          TEXT,
            prompt_tokens       INTEGER,
            completion_tokens   INTEGER,
            generated_at        TEXT NOT NULL,
            PRIMARY KEY (date, language)
        );
    """)
    conn.commit()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Collection runs ---

def create_collection_run(
    conn: sqlite3.Connection,
    query_hash: str,
    start_time: str,
    end_time: str,
) -> int:
    """Insert a new collection run and return its id."""
    cur = conn.execute(
        """INSERT INTO collection_runs (started_at, query_hash, start_time, end_time)
           VALUES (?, ?, ?, ?)""",
        (_now_iso(), query_hash, start_time, end_time),
    )
    conn.commit()
    return cur.lastrowid


def finish_collection_run(
    conn: sqlite3.Connection,
    run_id: int,
    tweets_fetched: int,
    tweets_new: int,
    status: str = "completed",
    error_message: str | None = None,
) -> None:
    conn.execute(
        """UPDATE collection_runs
           SET finished_at=?, tweets_fetched=?, tweets_new=?, status=?, error_message=?
           WHERE id=?""",
        (_now_iso(), tweets_fetched, tweets_new, status, error_message, run_id),
    )
    conn.commit()


# --- Users ---

def upsert_user(
    conn: sqlite3.Connection,
    user_data: dict,
    curated_usernames: set[str] | None = None,
) -> None:
    """Insert or update a user record."""
    now = _now_iso()
    uid = user_data["id"]
    username = user_data.get("username", "")
    pm = user_data.get("public_metrics", {})
    is_curated = 1 if curated_usernames and username.lower() in curated_usernames else 0

    conn.execute(
        """INSERT INTO users (user_id, name, username, description, profile_image_url,
                              verified, followers_count, following_count, tweet_count,
                              listed_count, is_curated, first_seen_at, last_updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
               name=excluded.name,
               username=excluded.username,
               description=excluded.description,
               profile_image_url=excluded.profile_image_url,
               verified=excluded.verified,
               followers_count=excluded.followers_count,
               following_count=excluded.following_count,
               tweet_count=excluded.tweet_count,
               listed_count=excluded.listed_count,
               is_curated=MAX(users.is_curated, excluded.is_curated),
               last_updated_at=excluded.last_updated_at""",
        (
            uid,
            user_data.get("name", ""),
            username,
            user_data.get("description", ""),
            user_data.get("profile_image_url", ""),
            1 if user_data.get("verified") else 0,
            pm.get("followers_count", 0),
            pm.get("following_count", 0),
            pm.get("tweet_count", 0),
            pm.get("listed_count", 0),
            is_curated,
            now,
            now,
        ),
    )


def insert_tweet(conn: sqlite3.Connection, tweet: dict, run_id: int) -> bool:
    """Insert a tweet. Returns True if it was new (not a duplicate)."""
    pm = tweet.get("public_metrics", {})
    now = _now_iso()

    try:
        conn.execute(
            """INSERT OR IGNORE INTO tweets
               (tweet_id, author_id, text, created_at, conversation_id,
                in_reply_to_user_id, lang, source,
                retweet_count, reply_count, like_count, quote_count,
                impression_count, bookmark_count,
                referenced_tweets, entities, context_annotations,
                collection_run_id, collected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tweet["id"],
                tweet.get("author_id", ""),
                tweet.get("text", ""),
                tweet.get("created_at", ""),
                tweet.get("conversation_id"),
                tweet.get("in_reply_to_user_id"),
                tweet.get("lang"),
                tweet.get("source"),
                pm.get("retweet_count", 0),
                pm.get("reply_count", 0),
                pm.get("like_count", 0),
                pm.get("quote_count", 0),
                pm.get("impression_count", 0),
                pm.get("bookmark_count", 0),
                json.dumps(tweet.get("referenced_tweets")) if tweet.get("referenced_tweets") else None,
                json.dumps(tweet.get("entities")) if tweet.get("entities") else None,
                json.dumps(tweet.get("context_annotations")) if tweet.get("context_annotations") else None,
                run_id,
                now,
            ),
        )
        return conn.total_changes > 0
    except sqlite3.IntegrityError:
        return False


def insert_tweets_batch(
    conn: sqlite3.Connection, tweets: list[dict], run_id: int
) -> tuple[int, int]:
    """Insert a batch of tweets. Returns (total_fetched, new_inserted)."""
    new_count = 0
    before = _count_tweets(conn)
    for tweet in tweets:
        insert_tweet(conn, tweet, run_id)
    after = _count_tweets(conn)
    new_count = after - before
    conn.commit()
    return len(tweets), new_count


def _count_tweets(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) FROM tweets").fetchone()
    return row[0]


# --- Daily briefs ---

def save_daily_brief(
    conn: sqlite3.Connection,
    date: str,
    language: str,
    brief_markdown: str,
    model_used: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO daily_briefs
           (date, language, brief_markdown, model_used, prompt_tokens, completion_tokens, generated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (date, language, brief_markdown, model_used, prompt_tokens, completion_tokens, _now_iso()),
    )
    conn.commit()


def get_daily_brief(conn: sqlite3.Connection, date: str, language: str = "en") -> str | None:
    row = conn.execute(
        "SELECT brief_markdown FROM daily_briefs WHERE date=? AND language=?",
        (date, language),
    ).fetchone()
    return row["brief_markdown"] if row else None
