"""The lazy spaCy loader must attempt the model once, not once per article."""

from __future__ import annotations

import finscrape.analysis.nlp as nlp_mod


def _reset():
    nlp_mod._nlp = None
    nlp_mod._nlp_unavailable = False


def test_missing_model_is_attempted_once(monkeypatch):
    attempts = []

    class FakeSpacy:
        @staticmethod
        def load(_name):
            attempts.append(1)
            raise OSError("model not installed")

    _reset()
    monkeypatch.setitem(__import__("sys").modules, "spacy", FakeSpacy)
    for _ in range(25):
        assert nlp_mod._get_nlp() is None
    assert len(attempts) == 1  # latched, not retried per call
    _reset()


def test_a_loaded_model_is_reused(monkeypatch):
    attempts = []
    sentinel = object()

    class FakeSpacy:
        @staticmethod
        def load(_name):
            attempts.append(1)
            return sentinel

    _reset()
    monkeypatch.setitem(__import__("sys").modules, "spacy", FakeSpacy)
    assert nlp_mod._get_nlp() is sentinel
    assert nlp_mod._get_nlp() is sentinel
    assert len(attempts) == 1
    _reset()
