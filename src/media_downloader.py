"""Download tweet images to local storage."""

import logging
from pathlib import Path

import requests

from src.config import get_db_path
from src.db import get_connection, get_undownloaded_media, update_media_local_path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = PROJECT_ROOT / "data" / "images"


def download_images(limit: int = 200) -> dict:
    """Download undownloaded media images to data/images/.

    Returns dict with download stats.
    """
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    db_path = get_db_path()
    conn = get_connection(db_path)

    media_items = get_undownloaded_media(conn, limit=limit)
    logger.info(f"Found {len(media_items)} images to download")

    downloaded = 0
    failed = 0

    for item in media_items:
        url = item["url"]
        media_key = item["media_key"]
        tweet_id = item["tweet_id"]

        filename = f"{tweet_id}_{media_key}.jpg"
        local_path = IMAGES_DIR / filename

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            local_path.write_bytes(resp.content)
            update_media_local_path(conn, media_key, str(local_path))
            conn.commit()
            downloaded += 1
            if downloaded % 20 == 0:
                logger.info(f"  Downloaded {downloaded}/{len(media_items)}...")
        except Exception as exc:
            logger.warning(f"  Failed to download {media_key}: {exc}")
            failed += 1

    conn.close()

    stats = {
        "total": len(media_items),
        "downloaded": downloaded,
        "failed": failed,
    }
    logger.info(f"Download complete: {stats}")
    return stats
