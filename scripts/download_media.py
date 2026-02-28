#!/usr/bin/env python3
"""Download tweet images that haven't been downloaded yet."""

import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.media_downloader import download_images

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Download tweet images")
    parser.add_argument("--limit", type=int, default=200, help="Max images to download")
    args = parser.parse_args()

    print("=" * 60)
    print("ASCO GU 2026 — Media Download")
    print("=" * 60)

    stats = download_images(limit=args.limit)

    print(f"\nResults: {stats['downloaded']} downloaded, {stats['failed']} failed out of {stats['total']}")


if __name__ == "__main__":
    main()
