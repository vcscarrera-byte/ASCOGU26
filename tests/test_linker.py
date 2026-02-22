"""Tests for linker — regex matching of abstract numbers in tweets."""

import pytest
from src.linker import find_abstract_numbers, _has_asco_context


class TestFindAbstractNumbers:
    def test_abstract_word(self):
        results = find_abstract_numbers("Great data from Abstract 305 on prostate cancer")
        nums = {r[0] for r in results}
        assert "305" in nums

    def test_abs_abbreviation(self):
        results = find_abstract_numbers("Abs 420 shows impressive PFS data")
        nums = {r[0] for r in results}
        assert "420" in nums

    def test_abstract_hash(self):
        results = find_abstract_numbers("Check out abstract #305")
        nums = {r[0] for r in results}
        assert "305" in nums

    def test_hashtag_with_context(self):
        results = find_abstract_numbers("#305 at #ASCOGU26 was impressive")
        nums = {r[0] for r in results}
        assert "305" in nums

    def test_hashtag_without_context(self):
        # Bare #305 without ASCO context should not match
        results = find_abstract_numbers("#305 is a great number")
        nums = {r[0] for r in results}
        assert "305" not in nums

    def test_multiple_numbers(self):
        results = find_abstract_numbers("Abstract 305 and Abs 420 both interesting")
        nums = {r[0] for r in results}
        assert "305" in nums
        assert "420" in nums

    def test_high_confidence_for_explicit(self):
        results = find_abstract_numbers("Abstract 305 data")
        conf = {r[0]: r[1] for r in results}
        assert conf["305"] == 1.0

    def test_lower_confidence_for_hashtag(self):
        results = find_abstract_numbers("#305 #GU26 presentation")
        conf = {r[0]: r[1] for r in results}
        assert conf["305"] == 0.8

    def test_no_match(self):
        results = find_abstract_numbers("Great conference this year")
        assert len(results) == 0

    def test_single_digit_ignored(self):
        # Too short (need 2-4 digits for explicit, 3-4 for hashtag)
        results = find_abstract_numbers("Abstract 5 is interesting")
        assert len(results) == 0

    def test_case_insensitive(self):
        results = find_abstract_numbers("ABSTRACT 305 data")
        nums = {r[0] for r in results}
        assert "305" in nums


class TestAscoContext:
    def test_gu26(self):
        assert _has_asco_context("#GU26 is great")

    def test_ascogu(self):
        assert _has_asco_context("at #ASCOGU this year")

    def test_ascogu26(self):
        assert _has_asco_context("#ASCOGU26 abstract")

    def test_no_context(self):
        assert not _has_asco_context("just a random tweet")
