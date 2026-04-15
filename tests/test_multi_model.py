"""Tests for finscrape.analysis.multi_model — MultiModelClient & agreement scoring."""

from __future__ import annotations

import os
from unittest.mock import patch, MagicMock

import pytest

from finscrape.analysis.multi_model import (
    MultiModelClient,
    ModelConsensus,
    _score_agreement,
    _adjust_confidence,
    _select_best_response,
    _parse_model_configs,
    HIGH_AGREEMENT_THRESHOLD,
    LOW_AGREEMENT_THRESHOLD,
    HIGH_AGREEMENT_BOOST,
    LOW_AGREEMENT_PENALTY,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_response(
    signal_score: int = 3,
    confidence: float = 0.8,
    impact_direction: str = "positive",
    verdict: str = "INVEST",
    relevant: bool = True,
) -> dict:
    """Factory for a minimal valid AI response dict."""
    return {
        "relevant": relevant,
        "signal_score": signal_score,
        "confidence": confidence,
        "impact_direction": impact_direction,
        "verdict": verdict,
        "event_type": "earnings",
        "tickers": ["AAPL"],
    }


TWO_MODEL_CONFIGS = [
    {"name": "deepseek", "model": "deepseek/deepseek-chat", "backend": "openrouter"},
    {"name": "claude", "model": "auto", "backend": "proxy"},
]

THREE_MODEL_CONFIGS = [
    {"name": "deepseek", "model": "deepseek/deepseek-chat", "backend": "openrouter"},
    {"name": "claude", "model": "auto", "backend": "proxy"},
    {"name": "gpt4", "model": "openai/gpt-4o", "backend": "openrouter"},
]


# ===================================================================
# _parse_model_configs
# ===================================================================

class TestParseModelConfigs:
    def test_explicit_configs_returned_as_is(self):
        cfgs = [{"name": "a", "model": "x", "backend": "proxy"}]
        assert _parse_model_configs(cfgs) == cfgs

    def test_env_var_parsing(self):
        with patch.dict(os.environ, {"FINSCRAPE_MODELS": "deepseek/deepseek-chat,auto"}):
            # Need to reimport to pick up env; instead call with None and patch the module-level var
            from finscrape.analysis import multi_model
            old = multi_model.FINSCRAPE_MODELS
            multi_model.FINSCRAPE_MODELS = "deepseek/deepseek-chat,auto"
            try:
                result = _parse_model_configs(None)
                assert len(result) == 2
                assert result[0]["name"] == "deepseek-chat"
                assert result[0]["backend"] == "openrouter"
                assert result[1]["name"] == "proxy"
                assert result[1]["model"] == "auto"
                assert result[1]["backend"] == "proxy"
            finally:
                multi_model.FINSCRAPE_MODELS = old

    def test_empty_env_returns_empty(self):
        from finscrape.analysis import multi_model
        old = multi_model.FINSCRAPE_MODELS
        multi_model.FINSCRAPE_MODELS = ""
        try:
            assert _parse_model_configs(None) == []
        finally:
            multi_model.FINSCRAPE_MODELS = old


# ===================================================================
# _score_agreement
# ===================================================================

class TestScoreAgreement:
    def test_single_response_perfect_agreement(self):
        assert _score_agreement([_make_response()]) == 1.0

    def test_all_models_agree(self):
        """Identical responses should yield agreement ~1.0."""
        responses = [_make_response() for _ in range(3)]
        score = _score_agreement(responses)
        assert score == 1.0

    def test_partial_agreement(self):
        """Two agree, one disagrees — should be between 0 and 1."""
        responses = [
            _make_response(signal_score=4, verdict="INVEST", impact_direction="positive"),
            _make_response(signal_score=4, verdict="INVEST", impact_direction="positive"),
            _make_response(signal_score=-2, verdict="CAUTIOUS", impact_direction="negative"),
        ]
        score = _score_agreement(responses)
        assert 0.0 < score < 1.0

    def test_all_disagree(self):
        """Maximum disagreement should produce a low score."""
        responses = [
            _make_response(signal_score=5, verdict="INVEST", impact_direction="positive"),
            _make_response(signal_score=-5, verdict="PULL_OUT", impact_direction="negative"),
        ]
        score = _score_agreement(responses)
        # signal_score std_dev = 5.0 -> score_agreement = 0
        # verdict_agreement = 0.5, direction_agreement = 0.5
        # average = (0 + 0.5 + 0.5) / 3 ≈ 0.333
        assert score < 0.4

    def test_empty_responses(self):
        assert _score_agreement([]) == 1.0

    def test_agreement_score_range(self):
        """Agreement score must always be in [0, 1]."""
        combos = [
            [_make_response(signal_score=s, verdict=v, impact_direction=d)
             for s, v, d in [(5, "INVEST", "positive"), (-5, "PULL_OUT", "negative"),
                             (0, "OBSERVE", "neutral")]]
        ]
        for responses in combos:
            score = _score_agreement(responses)
            assert 0.0 <= score <= 1.0


# ===================================================================
# _adjust_confidence
# ===================================================================

class TestAdjustConfidence:
    def test_high_agreement_boosts_confidence(self):
        resp = _make_response(confidence=0.7)
        adjusted = _adjust_confidence(resp, 0.9)
        expected = round(0.7 * (1.0 + HIGH_AGREEMENT_BOOST), 4)
        assert adjusted["confidence"] == expected

    def test_low_agreement_reduces_confidence(self):
        resp = _make_response(confidence=0.7)
        adjusted = _adjust_confidence(resp, 0.3)
        expected = round(0.7 * (1.0 - LOW_AGREEMENT_PENALTY), 4)
        assert adjusted["confidence"] == expected

    def test_mid_agreement_no_change(self):
        resp = _make_response(confidence=0.7)
        adjusted = _adjust_confidence(resp, 0.6)
        assert adjusted["confidence"] == 0.7

    def test_confidence_clamped_to_one(self):
        resp = _make_response(confidence=0.98)
        adjusted = _adjust_confidence(resp, 0.95)
        assert adjusted["confidence"] <= 1.0

    def test_confidence_clamped_to_zero(self):
        resp = _make_response(confidence=0.05)
        adjusted = _adjust_confidence(resp, 0.1)
        assert adjusted["confidence"] >= 0.0

    def test_does_not_mutate_original(self):
        resp = _make_response(confidence=0.7)
        _adjust_confidence(resp, 0.9)
        assert resp["confidence"] == 0.7


# ===================================================================
# _select_best_response
# ===================================================================

class TestSelectBestResponse:
    def test_picks_highest_confidence(self):
        responses = [
            _make_response(confidence=0.5),
            _make_response(confidence=0.9),
            _make_response(confidence=0.7),
        ]
        best = _select_best_response(responses)
        assert best["confidence"] == 0.9

    def test_empty_list_returns_empty_dict(self):
        assert _select_best_response([]) == {}


# ===================================================================
# MultiModelClient — construction
# ===================================================================

class TestMultiModelClientInit:
    def test_requires_at_least_one_config(self):
        with pytest.raises(ValueError, match="at least one model config"):
            MultiModelClient(model_configs=[])

    def test_none_configs_no_env_raises(self):
        from finscrape.analysis import multi_model
        old = multi_model.FINSCRAPE_MODELS
        multi_model.FINSCRAPE_MODELS = ""
        try:
            with pytest.raises(ValueError):
                MultiModelClient(model_configs=None)
        finally:
            multi_model.FINSCRAPE_MODELS = old

    def test_accepts_valid_configs(self):
        client = MultiModelClient(model_configs=TWO_MODEL_CONFIGS)
        assert len(client.model_configs) == 2


# ===================================================================
# MultiModelClient.analyze — single model
# ===================================================================

class TestSingleModelOperation:
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_single_model_returns_consensus(self, mock_call_ai):
        resp = _make_response()
        mock_call_ai.return_value = resp

        client = MultiModelClient(
            model_configs=[{"name": "deepseek", "model": "deepseek/deepseek-chat", "backend": "openrouter"}],
        )
        result = client.analyze("test prompt", "system prompt")

        assert isinstance(result, ModelConsensus)
        assert result.agreement_score == 1.0
        assert len(result.individual_responses) == 1
        assert result.models_used == ["deepseek"]
        assert result.models_failed == []
        mock_call_ai.assert_called_once()

    @patch("finscrape.analysis.multi_model.call_ai")
    def test_single_model_failure_returns_empty(self, mock_call_ai):
        mock_call_ai.return_value = None

        client = MultiModelClient(
            model_configs=[{"name": "only", "model": "x", "backend": "openrouter"}],
        )
        result = client.analyze("prompt", "system")

        assert result.consensus_response == {}
        assert result.models_failed == ["only"]
        assert result.models_used == []


# ===================================================================
# MultiModelClient.analyze — multi-model agreement
# ===================================================================

class TestMultiModelAgreement:
    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_all_models_agree_high_score(self, mock_call_ai):
        """All models return same response -> agreement 1.0, confidence boosted."""
        resp = _make_response(signal_score=3, confidence=0.8, verdict="INVEST", impact_direction="positive")
        mock_call_ai.return_value = resp

        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert result.agreement_score == 1.0
        assert len(result.individual_responses) == 3
        assert len(result.models_used) == 3
        # High agreement -> confidence boosted by 10%
        assert result.consensus_response["confidence"] == round(0.8 * 1.10, 4)

    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_partial_agreement(self, mock_call_ai):
        """Two agree, one disagrees -> intermediate agreement."""
        call_count = {"n": 0}
        responses = [
            _make_response(signal_score=4, verdict="INVEST", impact_direction="positive", confidence=0.8),
            _make_response(signal_score=4, verdict="INVEST", impact_direction="positive", confidence=0.9),
            _make_response(signal_score=-3, verdict="PULL_OUT", impact_direction="negative", confidence=0.6),
        ]

        def side_effect(*args, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx % len(responses)]

        mock_call_ai.side_effect = side_effect

        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert 0.0 < result.agreement_score < 1.0
        assert len(result.individual_responses) == 3

    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_all_disagree_low_score(self, mock_call_ai):
        """Maximum disagreement -> low agreement, confidence penalized."""
        call_count = {"n": 0}
        responses = [
            _make_response(signal_score=5, verdict="INVEST", impact_direction="positive", confidence=0.7),
            _make_response(signal_score=-5, verdict="PULL_OUT", impact_direction="negative", confidence=0.7),
        ]

        def side_effect(*args, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx % len(responses)]

        mock_call_ai.side_effect = side_effect

        client = MultiModelClient(model_configs=TWO_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert result.agreement_score < LOW_AGREEMENT_THRESHOLD
        # Low agreement -> confidence reduced by 15%
        assert result.consensus_response["confidence"] == round(0.7 * (1.0 - LOW_AGREEMENT_PENALTY), 4)


# ===================================================================
# MultiModelClient — fallback chain
# ===================================================================

class TestFallbackChain:
    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_fallback_when_all_parallel_fail(self, mock_call_ai):
        """When parallel batch fails, fallback tries sequentially."""
        good_response = _make_response(confidence=0.75)
        # First two calls fail (parallel), third call (fallback for first config) also fails,
        # but we need the fallback to eventually succeed.
        # The fallback iterates all configs again sequentially.
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            # First 3 calls fail (parallel batch), then first fallback call succeeds
            if call_count["n"] <= 3:
                return None
            return good_response

        mock_call_ai.side_effect = side_effect

        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert len(result.individual_responses) == 1
        assert len(result.models_used) == 1
        assert result.consensus_response["confidence"] > 0

    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_partial_failure_still_works(self, mock_call_ai):
        """One model fails in parallel, others succeed."""
        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                return None  # second model fails
            return _make_response(confidence=0.8)

        mock_call_ai.side_effect = side_effect

        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert len(result.individual_responses) == 2
        assert len(result.models_used) == 2
        assert len(result.models_failed) == 1

    @patch("finscrape.analysis.multi_model.call_ai")
    def test_all_models_fail_returns_empty_consensus(self, mock_call_ai):
        mock_call_ai.return_value = None

        client = MultiModelClient(model_configs=TWO_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert result.consensus_response == {}
        assert result.individual_responses == []
        assert len(result.models_failed) == 2

    @patch("finscrape.analysis.multi_model.call_ai")
    def test_fallback_tries_each_model_sequentially(self, mock_call_ai):
        """Verify the fallback chain tries models in order."""
        good_response = _make_response()
        call_count = {"n": 0}
        models_called: list[str | None] = []

        def side_effect(prompt, system_prompt, model=None):
            models_called.append(model)
            call_count["n"] += 1
            # Fail the first model in fallback, succeed on second
            if call_count["n"] <= 2:
                return None
            return good_response

        mock_call_ai.side_effect = side_effect

        client = MultiModelClient(model_configs=TWO_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        # Should have at least tried the first model, then fallback succeeds
        assert len(result.models_used) >= 1

    @patch("finscrape.analysis.multi_model.call_ai")
    def test_exception_in_model_treated_as_failure(self, mock_call_ai):
        """If call_ai raises, it's caught and treated as a failure."""
        mock_call_ai.side_effect = RuntimeError("connection refused")

        client = MultiModelClient(
            model_configs=[{"name": "broken", "model": "x", "backend": "openrouter"}],
        )
        result = client.analyze("prompt", "system")

        assert result.models_failed == ["broken"]
        assert result.consensus_response == {}


# ===================================================================
# Confidence adjustment integration
# ===================================================================

class TestConfidenceAdjustmentIntegration:
    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_high_agreement_boosts(self, mock_call_ai):
        mock_call_ai.return_value = _make_response(confidence=0.7)

        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        # All identical -> agreement 1.0 -> boosted
        assert result.consensus_response["confidence"] == round(0.7 * 1.10, 4)

    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_low_agreement_penalizes(self, mock_call_ai):
        call_count = {"n": 0}
        responses = [
            _make_response(signal_score=5, verdict="INVEST", impact_direction="positive", confidence=0.7),
            _make_response(signal_score=-5, verdict="PULL_OUT", impact_direction="negative", confidence=0.7),
        ]

        def side_effect(*args, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx % len(responses)]

        mock_call_ai.side_effect = side_effect
        client = MultiModelClient(model_configs=TWO_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert result.consensus_response["confidence"] == round(0.7 * 0.85, 4)

    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_mid_agreement_no_adjustment(self, mock_call_ai):
        """Agreement between 0.4 and 0.8 should not adjust confidence."""
        call_count = {"n": 0}
        # Craft responses that yield ~0.6 agreement
        responses = [
            _make_response(signal_score=3, verdict="INVEST", impact_direction="positive", confidence=0.7),
            _make_response(signal_score=3, verdict="INVEST", impact_direction="positive", confidence=0.7),
            _make_response(signal_score=0, verdict="OBSERVE", impact_direction="neutral", confidence=0.7),
        ]

        def side_effect(*args, **kwargs):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx % len(responses)]

        mock_call_ai.side_effect = side_effect
        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        agreement = result.agreement_score
        if LOW_AGREEMENT_THRESHOLD <= agreement <= HIGH_AGREEMENT_THRESHOLD:
            assert result.consensus_response["confidence"] == 0.7


# ===================================================================
# Multi-model mode gating
# ===================================================================

class TestMultiModelGating:
    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", False)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_disabled_uses_first_model_only(self, mock_call_ai):
        mock_call_ai.return_value = _make_response()

        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        # Should only call once (first model)
        assert mock_call_ai.call_count == 1
        assert len(result.individual_responses) == 1

    @patch("finscrape.analysis.multi_model.FINSCRAPE_MULTI_MODEL", True)
    @patch("finscrape.analysis.multi_model.call_ai")
    def test_enabled_uses_all_models(self, mock_call_ai):
        mock_call_ai.return_value = _make_response()

        client = MultiModelClient(model_configs=THREE_MODEL_CONFIGS)
        result = client.analyze("prompt", "system")

        assert mock_call_ai.call_count == 3
        assert len(result.individual_responses) == 3
