"""Fetch abstracts from ASCO GraphQL API and convert to structured rows."""

import logging
import time

import requests

logger = logging.getLogger(__name__)

ASCO_API_URL = "https://api.asco.org/graphql2"

# Public token (sub: "publictoken", name: "PublicAccess")
ASCO_AUTH_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJwdWJsaWN0b2tlbiIsIm5hbWUiOiJQdWJsaWNBY2Nlc3MiLCJzY29wZSI6ImFwaS5h"
    "c2NvLm9yZy9ncmFwaHFsLnB1YmxpYyIsImNsaWVudF9pZCI6InB1YmxpYyIsImlhdCI6MTc0NDIw"
    "NDU1N30.8j0ujB6vatkoI6w5sAnHY-ZjMN9h1bgDqlRe8E_lH2I"
)
ASCO_API_KEY = "da2-wgzqv6hk3bea3axyz6hslo33my"

ASCO_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.asco.org",
    "Referer": "https://www.asco.org/",
    "authorization": ASCO_AUTH_TOKEN,
    "x-api-key": ASCO_API_KEY,
}

ASCO_QUERY = """query MultiSearch($input: MultiSearchInput!) {
  search(input: $input) {
    status
    result {
      total
      hits {
        uid title abstractNumber body summary doi status score
        posterBoardNumber contentType styleType contentId contentSourceId presentationId
        meetingName titles
        cursor { uid score }
        contentUrl { path target title fqdn }
        primaryPerson { displayName role }
        date { start end timeZone }
        meeting { contentId name year }
        taxonomy { subjectsThes genesThes drugsThes orgThes entitiesThes countriesThes }
        highlights { body title }
        relatedMaterials { title contentId contentType sessionType contentUrl { path } }
      }
    }
    errors { code message }
  }
}"""


def fetch_abstracts_page(search_after=None) -> dict:
    """Fetch one page of abstracts (10 per page) via GraphQL."""
    variables = {
        "input": {
            "userInput": "*",
            "searchAfter": search_after,
            "filters": {
                "contentTypes": ["Presentation"],
                "mediaTypes": ["Abstracts"],
                "years": [],
            },
            "sortBy": "Relevancy",
            "contentKey": "GU",
            "contentKeyYear": 2026,
        }
    }
    payload = {
        "operationName": "MultiSearch",
        "variables": variables,
        "query": ASCO_QUERY,
    }
    r = requests.post(ASCO_API_URL, json=payload, headers=ASCO_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def extract_all_abstracts() -> list[dict]:
    """Extract all abstracts from ASCO GU 2026, paginating automatically.

    Returns list of raw GraphQL hits.
    """
    all_hits = []
    search_after = None
    page = 0

    logger.info("Fetching abstracts from ASCO GU 2026 API...")
    while True:
        page += 1
        data = fetch_abstracts_page(search_after)
        result = data["data"]["search"]["result"]
        hits = result["hits"]
        total = result["total"]

        if not hits:
            break

        all_hits.extend(hits)
        logger.info(f"  Page {page}: +{len(hits)} = {len(all_hits)}/{total}")

        if len(all_hits) >= total:
            break

        last = hits[-1]
        search_after = {
            "uid": last["cursor"]["uid"],
            "score": last["cursor"]["score"],
            "startDate": None,
            "dateTimePublished": None,
            "sessionTypeWeight": None,
            "primaryTrack": None,
            "abstractNumber": None,
        }
        time.sleep(0.3)

    logger.info(f"Fetched {len(all_hits)} abstracts")
    return all_hits


def abstracts_to_rows(hits: list[dict]) -> list[dict]:
    """Convert raw GraphQL hits to structured rows for DB import."""
    rows = []
    for h in hits:
        tax = h.get("taxonomy") or {}
        pp = h.get("primaryPerson") or {}
        cu = h.get("contentUrl") or {}
        dt = h.get("date") or {}
        rm = h.get("relatedMaterials") or []

        session_info = next(
            (r for r in rm if r.get("contentType") == "SESSION"), {}
        )

        rows.append({
            "abstract_number": h.get("abstractNumber") or "",
            "title": h.get("title") or "",
            "body": (h.get("body") or "").replace("\n", " ").strip(),
            "presenter": pp.get("displayName") or "",
            "presenter_role": pp.get("role") or "",
            "session_type": session_info.get("sessionType") or "",
            "session_title": session_info.get("title") or "",
            "poster_board_number": h.get("posterBoardNumber") or "",
            "doi": h.get("doi") or "",
            "date": dt.get("start") or "",
            "url": f"https://www.asco.org{cu['path']}" if cu.get("path") else "",
            "subjects": "; ".join(tax.get("subjectsThes") or []),
            "genes": "; ".join(tax.get("genesThes") or []),
            "drugs": "; ".join(tax.get("drugsThes") or []),
            "organizations": "; ".join(tax.get("orgThes") or []),
            "countries": "; ".join(tax.get("countriesThes") or []),
        })
    return rows
