"""
Multi-model LLM support with model agreement scoring.

Runs the same prompt through multiple LLM backends in parallel,
computes agreement scores across responses, and returns a consensus
result with confidence adjustments.

Configuration via environment variables:
  FINSCRAPE_MODELS      — comma-separated model identifiers
                           (e.g. "deepseek/deepseek-chat,auto")
  FINSCRAPE_MULTI_MODEL — "true" to enable multi-model mode (default "false")
"""

from __future__ import annotations

import logging
import math
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from finscrape.analysis.ai_client import call_ai

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment configuration
# ---------------------------------------------------------------------------

FINSCRAPE_MULTI_MODEL = os.getenv("FINSCRAPE_MULTI_MODEL", "false").lower() == "true"
FINSCRAPE_MODELS = os.getenv("FINSCRAPE_MODELS", "")

# Agreement thresholds for confidence adjustment
HIGH_AGREEMENT_THRESHOLD = 0.8
LOW_AGREEMENT_THRESHOLD = 0.4
HIGH_AGREEMENT_BOOST = 0.10     # +10% confidence
LOW_AGREEMENT_PENALTY = 0.15    # -15% confidence

# Maximum possible standard deviation for signal_score in [-5, 5]
_MAX_SCORE_STD_DEV = 5.0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ModelConsensus:
    """Result of multi-model analysis with agreement metrics."""

    consensus_response: dict = field(default_factory=dict)
    agreement_score: float = 0.0
    individual_responses: list[dict] = field(default_factory=list)
    models_used: list[str] = field(default_factory=list)
    models_failed: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Model config helpers
# ---------------------------------------------------------------------------

def _parse_model_configs(configs: list[dict[str, str]] | None = None) -> list[dict[str, str]]:
    """
    Return a list of model config dicts.

    If *configs* is provided, use it directly.  Otherwise fall back to the
    ``FINSCRAPE_MODELS`` env var (comma-separated model identifiers).  Each
    identifier becomes a config with ``backend`` inferred from the string:
    ``"auto"`` maps to ``"proxy"``, everything else to ``"openrouter"``.
    """
    if configs:
        return configs

    raw = FINSCRAPE_MODELS
    if not raw:
        return []

    result: list[dict[str, str]] = []
    for model_id in raw.split(","):
        model_id = model_id.strip()
        if not model_id:
            continue
        if model_id == "auto":
            result.append({"name": "proxy", "model": "auto", "backend": "proxy"})
        else:
            name = model_id.split("/")[-1] if "/" in model_id else model_id
            result.append({"name": name, "model": model_id, "backend": "openrouter"})
    return result


# ---------------------------------------------------------------------------
# Agreement scoring
# ---------------------------------------------------------------------------

def _score_agreement(responses: list[dict]) -> float:
    """
    Compute a model agreement score in [0.0, 1.0].

    The score is the average of three sub-scores:
      1. signal_score agreement  — 1 - (std_dev / MAX_STD_DEV)
      2. verdict agreement       — fraction of models sharing the majority verdict
      3. impact_direction agree.  — fraction sharing the majority direction
    """
    if len(responses) <= 1:
        return 1.0

    # --- signal_score agreement ---
    scores = [r.get("signal_score", 0) for r in responses]
    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    std_dev = math.sqrt(variance)
    score_agreement = max(0.0, 1.0 - (std_dev / _MAX_SCORE_STD_DEV))

    # --- verdict agreement ---
    verdicts = [r.get("verdict", r.get("consensus_verdict", "unknown")) for r in responses]
    if verdicts:
        most_common_verdict = max(set(verdicts), key=verdicts.count)
        verdict_agreement = verdicts.count(most_common_verdict) / len(verdicts)
    else:
        verdict_agreement = 1.0

    # --- impact_direction agreement ---
    directions = [r.get("impact_direction", "neutral") for r in responses]
    if directions:
        most_common_dir = max(set(directions), key=directions.count)
        direction_agreement = directions.count(most_common_dir) / len(directions)
    else:
        direction_agreement = 1.0

    return round((score_agreement + verdict_agreement + direction_agreement) / 3.0, 4)


def _adjust_confidence(response: dict, agreement_score: float) -> dict:
    """
    Return a copy of *response* with confidence adjusted by agreement level.

    - agreement > 0.8 ⟶ boost confidence by 10%
    - agreement < 0.4 ⟶ reduce confidence by 15%
    """
    result = dict(response)
    confidence = result.get("confidence", 0.5)

    if agreement_score > HIGH_AGREEMENT_THRESHOLD:
        confidence = confidence * (1.0 + HIGH_AGREEMENT_BOOST)
    elif agreement_score < LOW_AGREEMENT_THRESHOLD:
        confidence = confidence * (1.0 - LOW_AGREEMENT_PENALTY)

    result["confidence"] = round(max(0.0, min(1.0, confidence)), 4)
    return result


def _select_best_response(responses: list[dict]) -> dict:
    """Pick the response with the highest confidence as the consensus base."""
    if not responses:
        return {}
    return max(responses, key=lambda r: r.get("confidence", 0.0))


# ---------------------------------------------------------------------------
# MultiModelClient
# ---------------------------------------------------------------------------

class MultiModelClient:
    """
    Run the same prompt through multiple LLM models in parallel,
    collect responses, compute agreement, and return a consensus.

    Supports a fallback chain: if the primary model fails the next
    one in the list is tried, ensuring at least one response is
    returned when possible.

    Parameters
    ----------
    model_configs : list[dict]
        Each dict has keys ``name``, ``model``, and ``backend``.
    max_workers : int | None
        Thread-pool size (defaults to number of models, capped at 8).
    """

    def __init__(
        self,
        model_configs: list[dict[str, str]] | None = None,
        max_workers: int | None = None,
    ):
        self.model_configs = _parse_model_configs(model_configs)
        if not self.model_configs:
            raise ValueError(
                "MultiModelClient requires at least one model config. "
                "Pass model_configs or set FINSCRAPE_MODELS env var."
            )
        self.max_workers = max_workers or min(len(self.model_configs), 8)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        prompt: str,
        system_prompt: str,
    ) -> ModelConsensus:
        """
        Send *prompt* to every configured model in parallel and return
        a :class:`ModelConsensus` with agreement metrics.

        If multi-model mode is disabled (``FINSCRAPE_MULTI_MODEL != "true"``),
        only the first model in the config list is used.
        """
        configs_to_use = (
            self.model_configs
            if FINSCRAPE_MULTI_MODEL or len(self.model_configs) == 1
            else self.model_configs[:1]
        )

        individual_responses, models_used, models_failed = self._run_models(
            configs_to_use, prompt, system_prompt,
        )

        # Fallback chain: if every model in the parallel batch failed,
        # try remaining configs sequentially.
        if not individual_responses:
            individual_responses, models_used, models_failed = self._fallback_chain(
                prompt, system_prompt,
            )

        if not individual_responses:
            return ModelConsensus(
                models_failed=[c["name"] for c in self.model_configs],
            )

        agreement_score = _score_agreement(individual_responses)
        best = _select_best_response(individual_responses)
        consensus = _adjust_confidence(best, agreement_score)

        return ModelConsensus(
            consensus_response=consensus,
            agreement_score=agreement_score,
            individual_responses=individual_responses,
            models_used=models_used,
            models_failed=models_failed,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_single_model(
        self,
        config: dict[str, str],
        prompt: str,
        system_prompt: str,
    ) -> dict | None:
        """Invoke :func:`call_ai` for one model config."""
        model_id = config.get("model")
        try:
            return call_ai(prompt, system_prompt, model=model_id)
        except Exception as exc:
            logger.error("Model '%s' raised: %s", config.get("name"), exc)
            return None

    def _run_models(
        self,
        configs: list[dict[str, str]],
        prompt: str,
        system_prompt: str,
    ) -> tuple[list[dict], list[str], list[str]]:
        """Run models in parallel and partition results."""
        responses: list[dict] = []
        used: list[str] = []
        failed: list[str] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_cfg = {
                executor.submit(self._call_single_model, cfg, prompt, system_prompt): cfg
                for cfg in configs
            }
            for future in as_completed(future_to_cfg):
                cfg = future_to_cfg[future]
                name = cfg.get("name", "unknown")
                try:
                    result = future.result()
                    if result is not None:
                        responses.append(result)
                        used.append(name)
                    else:
                        failed.append(name)
                except Exception as exc:
                    logger.error("Model '%s' future raised: %s", name, exc)
                    failed.append(name)

        return responses, used, failed

    def _fallback_chain(
        self,
        prompt: str,
        system_prompt: str,
    ) -> tuple[list[dict], list[str], list[str]]:
        """Try each model sequentially until one succeeds."""
        failed: list[str] = []
        for cfg in self.model_configs:
            name = cfg.get("name", "unknown")
            result = self._call_single_model(cfg, prompt, system_prompt)
            if result is not None:
                return [result], [name], failed
            failed.append(name)
        return [], [], failed
