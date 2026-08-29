"""
Confidence Scorer for Council Agents
Synthesized from claude-council and geopolitics-ml patterns

Features:
- Multi-agent confidence aggregation
- Historical accuracy tracking
- Calibration scoring
- Bias detection
- Dynamic weight adjustment
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
from collections import Counter
import time
import math


class ConfidenceLevel(Enum):
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class AgentPrediction:
    """Prediction from a council agent"""
    agent_id: str
    prediction: str
    confidence: float  # 0-1
    reasoning: str
    timestamp: float
    metadata: Dict[str, any]


@dataclass
class PredictionOutcome:
    """Actual outcome for a prediction"""
    prediction_id: str
    outcome: str
    timestamp: float
    accuracy: float  # 0-1


@dataclass
class AgentPerformance:
    """Historical performance of an agent"""
    agent_id: str
    total_predictions: int
    correct_predictions: int
    accuracy: float
    average_confidence: float
    calibration_score: float  # How well confidence matches accuracy
    bias_score: float  # Tendency to be over/under confident
    recent_trend: str  # 'improving', 'stable', 'declining'


@dataclass
class ConfidenceScore:
    """Aggregated confidence score"""
    prediction_id: str
    consensus_prediction: str
    weighted_confidence: float
    agent_scores: Dict[str, float]
    agreement_score: float  # How much agents agree
    confidence_level: ConfidenceLevel
    risk_factors: List[str]
    recommendation: str


class ConfidenceScorer:
    """
    Meta-confidence scoring for council agents
    Synthesized from claude-council and geopolitics-ml patterns
    """
    
    def __init__(self):
        self.agent_history: Dict[str, List[Tuple[str, float, bool]]] = {}  # agent_id -> [(prediction, confidence, correct)]
        self.prediction_history: List[Dict[str, any]] = []
        self.calibration_bins: Dict[str, List[Tuple[float, bool]]] = {}  # agent_id -> [(confidence, correct)]
    
    def record_prediction(
        self,
        prediction: AgentPrediction,
        outcome: Optional[PredictionOutcome] = None
    ):
        """Record an agent prediction"""
        agent_id = prediction.agent_id
        
        if agent_id not in self.agent_history:
            self.agent_history[agent_id] = []
            self.calibration_bins[agent_id] = []
        
        # Record prediction
        correct = outcome.accuracy > 0.5 if outcome else None
        self.agent_history[agent_id].append((
            prediction.prediction,
            prediction.confidence,
            correct
        ))
        
        # Record for calibration
        if outcome:
            self.calibration_bins[agent_id].append((
                prediction.confidence,
                outcome.accuracy > 0.5
            ))
    
    def calculate_agent_performance(self, agent_id: str) -> AgentPerformance:
        """Calculate performance metrics for an agent"""
        history = self.agent_history.get(agent_id, [])
        
        if not history:
            return AgentPerformance(
                agent_id=agent_id,
                total_predictions=0,
                correct_predictions=0,
                accuracy=0,
                average_confidence=0,
                calibration_score=0,
                bias_score=0,
                recent_trend='unknown'
            )
        
        total = len(history)
        correct = sum(1 for _, _, c in history if c is True)
        avg_confidence = sum(c for _, c, _ in history) / total
        
        # Calculate calibration score
        calibration_bins = self.calibration_bins.get(agent_id, [])
        calibration_score = self._calculate_calibration(calibration_bins)
        
        # Calculate bias score
        bias_score = self._calculate_bias(calibration_bins)
        
        # Calculate recent trend
        recent_trend = self._calculate_trend(history)
        
        return AgentPerformance(
            agent_id=agent_id,
            total_predictions=total,
            correct_predictions=correct,
            accuracy=correct / total if total > 0 else 0,
            average_confidence=avg_confidence,
            calibration_score=calibration_score,
            bias_score=bias_score,
            recent_trend=recent_trend
        )
    
    def _calculate_calibration(self, bins: List[Tuple[float, bool]]) -> float:
        """
        Calculate calibration score (how well confidence matches accuracy)
        Perfect calibration: confidence == accuracy for all predictions
        """
        if not bins:
            return 0
        
        # Group by confidence buckets (0-0.2, 0.2-0.4, etc.)
        buckets: Dict[int, List[bool]] = {}
        for confidence, correct in bins:
            bucket = int(confidence * 5)  # 0-4
            if bucket not in buckets:
                buckets[bucket] = []
            buckets[bucket].append(correct)
        
        # Calculate calibration error
        total_error = 0
        total_predictions = 0
        
        for bucket, outcomes in buckets.items():
            expected_confidence = (bucket + 0.5) / 5  # Midpoint of bucket
            actual_accuracy = sum(outcomes) / len(outcomes)
            error = abs(expected_confidence - actual_accuracy)
            total_error += error * len(outcomes)
            total_predictions += len(outcomes)
        
        if total_predictions == 0:
            return 0
        
        # Calibration score (1 = perfect, 0 = worst)
        return 1 - (total_error / total_predictions)
    
    def _calculate_bias(self, bins: List[Tuple[float, bool]]) -> float:
        """
        Calculate bias score
        Positive = overconfident, Negative = underconfident
        """
        if not bins:
            return 0
        
        total_confidence = sum(c for c, _ in bins)
        total_accuracy = sum(1 for _, c in bins if c) / len(bins)
        
        # Bias = average confidence - average accuracy
        return (total_confidence / len(bins)) - total_accuracy
    
    def _calculate_trend(self, history: List[Tuple[str, float, Optional[bool]]]) -> str:
        """Calculate recent performance trend"""
        if len(history) < 10:
            return 'insufficient_data'
        
        # Compare recent vs older performance
        recent = history[-10:]
        older = history[-20:-10] if len(history) >= 20 else history[:10]
        
        recent_correct = sum(1 for _, _, c in recent if c is True) / len(recent)
        older_correct = sum(1 for _, _, c in older if c is True) / len(older) if older else 0
        
        diff = recent_correct - older_correct
        
        if diff > 0.1:
            return 'improving'
        elif diff < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def aggregate_predictions(
        self,
        predictions: List[AgentPrediction]
    ) -> ConfidenceScore:
        """Aggregate predictions from multiple agents"""
        if not predictions:
            return ConfidenceScore(
                prediction_id '',
                consensus_prediction='insufficient_data',
                weighted_confidence=0,
                agent_scores={},
                agreement_score=0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                risk_factors=['No predictions available'],
                recommendation='Wait for more agent predictions'
            )
        
        # Calculate agent weights based on performance
        agent_weights = {}
        for pred in predictions:
            performance = self.calculate_agent_performance(pred.agent_id)
            # Weight based on accuracy and calibration
            weight = performance.accuracy * performance.calibration_score
            agent_weights[pred.agent_id] = max(0.1, weight)  # Minimum weight
        
        # Normalize weights
        total_weight = sum(agent_weights.values())
        agent_weights = {k: v / total_weight for k, v in agent_weights.items()}
        
        # Calculate weighted confidence
        weighted_confidence = sum(
            pred.confidence * agent_weights.get(pred.agent_id, 0.1)
            for pred in predictions
        )
        
        # Calculate agreement score
        predictions_list = [pred.prediction for pred in predictions]
        unique_predictions = set(predictions_list)
        agreement_score = 1 - (len(unique_predictions) - 1) / max(1, len(predictions) - 1)
        
        # Find consensus prediction (most common)
        prediction_counts = Counter(predictions_list)
        consensus_prediction = prediction_counts.most_common(1)[0][0]
        
        # Determine confidence level
        if weighted_confidence >= 0.9:
            confidence_level = ConfidenceLevel.VERY_HIGH
        elif weighted_confidence >= 0.7:
            confidence_level = ConfidenceLevel.HIGH
        elif weighted_confidence >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        elif weighted_confidence >= 0.3:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW
        
        # Identify risk factors
        risk_factors = []
        if agreement_score < 0.5:
            risk_factors.append('Low agent agreement')
        if weighted_confidence < 0.5:
            risk_factors.append('Low overall confidence')
        
        for pred in predictions:
            if pred.confidence < 0.3:
                risk_factors.append(f'{pred.agent_id} has very low confidence')
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            confidence_level, agreement_score, risk_factors
        )
        
        return ConfidenceScore(
            prediction_id=f'pred_{int(time.time())}',
            consensus_prediction=consensus_prediction,
            weighted_confidence=weighted_confidence,
            agent_scores=agent_weights,
            agreement_score=agreement_score,
            confidence_level=confidence_level,
            risk_factors=risk_factors,
            recommendation=recommendation
        )
    
    def _generate_recommendation(
        self,
        confidence_level: ConfidenceLevel,
        agreement_score: float,
        risk_factors: List[str]
    ) -> str:
        """Generate recommendation based on confidence analysis"""
        if confidence_level == ConfidenceLevel.VERY_HIGH and agreement_score > 0.8:
            return 'High confidence consensus. Safe to proceed with strong conviction.'
        elif confidence_level == ConfidenceLevel.HIGH and agreement_score > 0.6:
            return 'Good consensus with reasonable confidence. Proceed with caution.'
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return 'Moderate confidence. Consider additional verification before major decisions.'
        elif confidence_level == ConfidenceLevel.LOW or agreement_score < 0.4:
            return 'Low confidence or significant disagreement. Seek additional information.'
        else:
            return 'Very low confidence. Do not proceed without significant additional verification.'
    
    def get_agent_rankings(self) -> List[AgentPerformance]:
        """Get ranked list of agent performances"""
        performances = []
        for agent_id in self.agent_history.keys():
            performance = self.calculate_agent_performance(agent_id)
            performances.append(performance)
        
        # Sort by accuracy * calibration
        performances.sort(
            key=lambda p: p.accuracy * p.calibration_score,
            reverse=True
        )
        
        return performances