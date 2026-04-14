"""Tests for src.api.search_classifier.is_natural_language."""
from src.api.search_classifier import is_natural_language


# ----- positive cases -----

def test_long_query_is_nl():
    assert is_natural_language("show me a stack for building a local rag app please")


def test_action_verb_build():
    assert is_natural_language("I want to build a vector database")


def test_phrase_how_do_i():
    assert is_natural_language("how do I parse PDFs?")


def test_question_mark_short():
    assert is_natural_language("fastapi?")


def test_phrase_looking_for():
    assert is_natural_language("looking for an LLM runtime")


def test_help_me_phrase():
    assert is_natural_language("help me pick a framework")


# ----- negative cases -----

def test_single_keyword():
    assert not is_natural_language("fastapi")


def test_two_keywords():
    assert not is_natural_language("qdrant vector db")


def test_three_keywords():
    assert not is_natural_language("react hooks library")


# ----- edges -----

def test_empty_string():
    assert not is_natural_language("")


def test_whitespace_only():
    assert not is_natural_language("   ")


def test_all_caps_keyword():
    assert not is_natural_language("FASTAPI")


def test_all_caps_with_verb():
    # "BUILD" — verb match is case-insensitive
    assert is_natural_language("BUILD ME A RAG APP")


def test_punctuation_only_non_question():
    assert not is_natural_language("...")


def test_question_mark_string_is_nl():
    # Rule: ends with '?' -> NL
    assert is_natural_language("???")


def test_hyphenated_keyword_pair():
    assert not is_natural_language("machine-learning toolkit")
