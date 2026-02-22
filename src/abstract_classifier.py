"""Classify abstracts by tumor type and session importance."""

import re

# Deterministic mapping from session title keywords to tumor types.
# Order matters: first match wins.
TUMOR_PATTERNS: list[tuple[str, list[str]]] = [
    ("Prostate", [
        "prostate cancer", "prostate", "localized prostate", "advanced prostate",
    ]),
    ("Bladder / Urothelial", [
        "urothelial carcinoma", "urothelial", "bladder cancer", "bladder",
        "bladder preservation", "non-muscle-invasive bladder",
        "muscle-invasive bladder", "nmibc", "mibc",
    ]),
    ("Kidney / RCC", [
        "renal cell cancer", "renal cell carcinoma", "kidney cancer",
        "kidney", "rcc",
    ]),
    ("Testicular / Germ Cell", [
        "testicular", "germ cell", "seminoma",
    ]),
    ("Other GU", [
        "penile", "adrenal", "urethral",
    ]),
]

SESSION_RANKS: dict[str, int] = {
    "Oral Abstract Session": 5,
    "Rapid Oral Abstract Session": 4,
    "General Session": 3,
    "Poster Walks": 2,
    "Poster Session": 1,
    "Trials in Progress Poster Session": 1,
    "Networking Event": 0,
}


def classify_tumor_from_session(
    session_title: str,
    title: str = "",
    body: str = "",
) -> str:
    """Infer the primary tumor type from session title, abstract title, or body.

    Returns the tumor type string (e.g., 'Prostate') or '' if unknown.
    Priority: session_title > title > body.
    """
    for text in [session_title, title, body]:
        if not text:
            continue
        text_lower = text.lower()
        for tumor_type, keywords in TUMOR_PATTERNS:
            for kw in keywords:
                if kw.lower() in text_lower:
                    return tumor_type
    return ""


def get_session_rank(session_type: str) -> int:
    """Return importance rank for a session type.

    Oral=5, Rapid Oral=4, General=3, Poster Walks=2, Poster/TIP=1, Networking=0.
    """
    return SESSION_RANKS.get(session_type, 1)
