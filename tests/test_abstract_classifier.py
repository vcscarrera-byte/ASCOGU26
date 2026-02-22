"""Tests for abstract_classifier — tumor inference and session ranking."""

import pytest
from src.abstract_classifier import classify_tumor_from_session, get_session_rank


class TestClassifyTumor:
    def test_prostate_from_session(self):
        assert classify_tumor_from_session("Oral Abstract Session A: Prostate Cancer") == "Prostate"

    def test_bladder_from_session(self):
        assert classify_tumor_from_session("Poster Session B: Urothelial Carcinoma") == "Bladder / Urothelial"

    def test_bladder_nmibc(self):
        result = classify_tumor_from_session(
            "Non-Muscle-Invasive Bladder Cancer Management"
        )
        assert result == "Bladder / Urothelial"

    def test_kidney_from_session(self):
        assert classify_tumor_from_session("Poster Session C: Renal Cell Cancer") == "Kidney / RCC"

    def test_testicular_from_session(self):
        result = classify_tumor_from_session(
            "Poster Session C: Renal Cell Cancer; Adrenal, Penile, Testicular and Urethral Cancers"
        )
        # RCC comes first in our pattern order
        assert result == "Kidney / RCC"

    def test_testicular_direct(self):
        result = classify_tumor_from_session("Poster Session: Testicular Cancer")
        assert result == "Testicular / Germ Cell"

    def test_fallback_to_title(self):
        result = classify_tumor_from_session(
            "Networking Event",
            title="Novel approaches in prostate cancer treatment",
        )
        assert result == "Prostate"

    def test_fallback_to_body(self):
        result = classify_tumor_from_session(
            "Networking Event",
            title="Discussion panel",
            body="This study evaluates outcomes in renal cell carcinoma patients",
        )
        assert result == "Kidney / RCC"

    def test_unknown_returns_empty(self):
        assert classify_tumor_from_session("Networking Event") == ""

    def test_case_insensitive(self):
        assert classify_tumor_from_session("PROSTATE CANCER session") == "Prostate"

    def test_empty_input(self):
        assert classify_tumor_from_session("") == ""


class TestSessionRank:
    def test_oral(self):
        assert get_session_rank("Oral Abstract Session") == 5

    def test_rapid_oral(self):
        assert get_session_rank("Rapid Oral Abstract Session") == 4

    def test_general(self):
        assert get_session_rank("General Session") == 3

    def test_poster_walks(self):
        assert get_session_rank("Poster Walks") == 2

    def test_poster(self):
        assert get_session_rank("Poster Session") == 1

    def test_tip(self):
        assert get_session_rank("Trials in Progress Poster Session") == 1

    def test_networking(self):
        assert get_session_rank("Networking Event") == 0

    def test_unknown_defaults_to_1(self):
        assert get_session_rank("Something New") == 1
