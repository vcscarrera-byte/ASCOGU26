"""Tests for clinical filters module."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.clinical_filters import (
    build_text_filter_clause,
    classify_tweet_text,
    get_drug_names,
    get_tumor_type_names,
)


def test_get_tumor_type_names():
    names = get_tumor_type_names()
    assert "Prostate" in names
    assert "Bladder / Urothelial" in names
    assert "Kidney / RCC" in names


def test_get_drug_names():
    names = get_drug_names()
    assert "pembrolizumab" in names
    assert "enzalutamide" in names
    assert len(names) >= 20
    # Should be sorted
    assert names == sorted(names)


def test_build_filter_empty_selection():
    """No filters selected → empty clause."""
    clause, params = build_text_filter_clause(None, None)
    assert clause == ""
    assert params == []

    clause, params = build_text_filter_clause([], [])
    assert clause == ""
    assert params == []


def test_build_filter_tumor_only():
    """Single tumor type → OR of synonyms."""
    clause, params = build_text_filter_clause(["Prostate"], None)
    assert clause != ""
    assert "LOWER" in clause
    assert "LIKE" in clause
    # Should have params for each synonym (prostate, mCRPC, mHSPC, etc.)
    assert len(params) >= 3
    assert "%prostate%" in params


def test_build_filter_drug_only():
    """Single drug → OR of synonyms."""
    clause, params = build_text_filter_clause(None, ["pembrolizumab"])
    assert clause != ""
    assert "%pembrolizumab%" in params
    assert "%keytruda%" in params


def test_build_filter_tumor_and_drug():
    """Both tumor and drug → AND between groups."""
    clause, params = build_text_filter_clause(["Prostate"], ["enzalutamide"])
    assert " AND " in clause
    # Should have tumor synonyms + drug synonyms
    assert "%prostate%" in params
    assert "%enzalutamide%" in params


def test_build_filter_multiple_tumors():
    """Multiple tumors → all synonyms OR-ed together."""
    clause, params = build_text_filter_clause(
        ["Prostate", "Kidney / RCC"], None
    )
    assert clause != ""
    assert "%prostate%" in params
    assert "%kidney%" in params
    assert "%renal%" in params


def test_build_filter_multiple_drugs():
    """Multiple drugs → all synonyms OR-ed together."""
    clause, params = build_text_filter_clause(
        None, ["pembrolizumab", "nivolumab"]
    )
    assert clause != ""
    assert "%pembrolizumab%" in params
    assert "%keytruda%" in params
    assert "%nivolumab%" in params
    assert "%opdivo%" in params


def test_classify_prostate_tweet():
    text = "Exciting data on enzalutamide in mCRPC patients at #ASCOGU26"
    result = classify_tweet_text(text)
    assert "Prostate" in result["tumor_types"]
    assert "enzalutamide" in result["drugs"]


def test_classify_kidney_tweet():
    text = "Pembrolizumab + lenvatinib in renal cell carcinoma shows OS benefit"
    result = classify_tweet_text(text)
    assert "Kidney / RCC" in result["tumor_types"]
    assert "pembrolizumab" in result["drugs"]
    assert "lenvatinib" in result["drugs"]


def test_classify_bladder_tweet():
    text = "Enfortumab vedotin in urothelial cancer - game changing data!"
    result = classify_tweet_text(text)
    assert "Bladder / Urothelial" in result["tumor_types"]
    assert "enfortumab vedotin" in result["drugs"]


def test_classify_no_match():
    text = "Great weather today at #ASCOGU26 in San Francisco!"
    result = classify_tweet_text(text)
    assert result["tumor_types"] == []
    assert result["drugs"] == []


def test_classify_brand_name():
    text = "Keytruda approved for new indication in bladder cancer"
    result = classify_tweet_text(text)
    assert "pembrolizumab" in result["drugs"]
    assert "Bladder / Urothelial" in result["tumor_types"]


def test_classify_case_insensitive():
    text = "PEMBROLIZUMAB data in PROSTATE cancer"
    result = classify_tweet_text(text)
    assert "Prostate" in result["tumor_types"]
    assert "pembrolizumab" in result["drugs"]


def test_classify_multiple_tumors():
    text = "Cross-tumor analysis of nivolumab in prostate and kidney cancer"
    result = classify_tweet_text(text)
    assert "Prostate" in result["tumor_types"]
    assert "Kidney / RCC" in result["tumor_types"]
    assert "nivolumab" in result["drugs"]


def test_classify_lu_psma():
    text = "Lu-PSMA radioligand therapy shows benefit in mCRPC"
    result = classify_tweet_text(text)
    assert "Lu-PSMA" in result["drugs"]
    assert "Prostate" in result["tumor_types"]
