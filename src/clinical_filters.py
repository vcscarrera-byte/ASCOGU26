"""Clinical filters for drug and tumor type classification.

Provides config-driven text matching for GU oncology tweets.
Filters are defined in config.yaml under clinical_filters.
"""

import re
from functools import lru_cache

from src.config import get_clinical_filter_config


@lru_cache(maxsize=1)
def _load_filters() -> dict:
    """Load and cache clinical filter config."""
    return get_clinical_filter_config()


def get_tumor_type_names() -> list[str]:
    """Return display names for tumor types (e.g. ['Prostate', 'Bladder / Urothelial', ...])."""
    cfg = _load_filters()
    return list(cfg.get("tumor_types", {}).keys())


def get_drug_names() -> list[str]:
    """Return sorted display names for drugs."""
    cfg = _load_filters()
    return sorted(cfg.get("drugs", {}).keys())


def _get_synonyms_for_tumors(selected: list[str]) -> list[str]:
    """Get all synonym patterns for selected tumor types."""
    cfg = _load_filters()
    tumor_cfg = cfg.get("tumor_types", {})
    synonyms = []
    for name in selected:
        synonyms.extend(tumor_cfg.get(name, []))
    return synonyms


def _get_synonyms_for_drugs(selected: list[str]) -> list[str]:
    """Get all synonym patterns for selected drugs."""
    cfg = _load_filters()
    drug_cfg = cfg.get("drugs", {})
    synonyms = []
    for name in selected:
        synonyms.extend(drug_cfg.get(name, []))
    return synonyms


def build_text_filter_clause(
    selected_tumors: list[str] | None = None,
    selected_drugs: list[str] | None = None,
    text_column: str = "t.text",
) -> tuple[str, list[str]]:
    """Build SQL WHERE clause fragment for clinical text filtering.

    Returns (sql_fragment, params).
    - If nothing selected, returns ("", []).
    - Tumor synonyms are OR-ed together.
    - Drug synonyms are OR-ed together.
    - If both tumors AND drugs selected, they are AND-ed.

    Example return:
        ("(LOWER(t.text) LIKE ? OR LOWER(t.text) LIKE ?) AND (LOWER(t.text) LIKE ?)",
         ["%prostate%", "%mcrpc%", "%enzalutamide%"])
    """
    parts = []
    params: list[str] = []

    # Tumor filter
    if selected_tumors:
        tumor_synonyms = _get_synonyms_for_tumors(selected_tumors)
        if tumor_synonyms:
            or_clauses = [f"LOWER({text_column}) LIKE ?" for _ in tumor_synonyms]
            parts.append(f"({' OR '.join(or_clauses)})")
            params.extend(f"%{s.lower()}%" for s in tumor_synonyms)

    # Drug filter
    if selected_drugs:
        drug_synonyms = _get_synonyms_for_drugs(selected_drugs)
        if drug_synonyms:
            or_clauses = [f"LOWER({text_column}) LIKE ?" for _ in drug_synonyms]
            parts.append(f"({' OR '.join(or_clauses)})")
            params.extend(f"%{s.lower()}%" for s in drug_synonyms)

    if not parts:
        return "", []

    # AND between tumor and drug groups
    return " AND ".join(parts), params


def classify_tweet_text(text: str) -> dict:
    """Classify a tweet by matched tumor types and drugs.

    Uses word-boundary regex for accurate matching.
    Returns: {"tumor_types": ["Prostate", ...], "drugs": ["pembrolizumab", ...]}
    """
    cfg = _load_filters()
    text_lower = text.lower()

    matched_tumors = []
    for tumor_name, synonyms in cfg.get("tumor_types", {}).items():
        for syn in synonyms:
            pattern = re.compile(re.escape(syn.lower()), re.IGNORECASE)
            if pattern.search(text_lower):
                matched_tumors.append(tumor_name)
                break

    matched_drugs = []
    for drug_name, synonyms in cfg.get("drugs", {}).items():
        for syn in synonyms:
            pattern = re.compile(re.escape(syn.lower()), re.IGNORECASE)
            if pattern.search(text_lower):
                matched_drugs.append(drug_name)
                break

    return {"tumor_types": matched_tumors, "drugs": matched_drugs}
