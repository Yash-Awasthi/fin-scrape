"""
核心服务单元测试 — relationship_service, calibration_service, scenario_script_engine
"""
import pytest
import uuid
import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.models.raw_news import RawNews
from backend.models.news_cluster import NewsCluster
from backend.models.ir_event import AbstractIRGEvent
from backend.models.event_relationship import EventRelationship
from backend.models.scenario import ScenarioScript, ScenarioStep
from backend.models.prediction import PredictionRun
from backend.models.outcome import ActualOutcome, PredictionEvaluation
from backend.models.theory_analysis import TheoryAnalysis
from backend.models.inference_layer import ActorProfile, TriggerRule, ConstraintRule


@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(test_engine):
    Session = sessionmaker(bind=test_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _create_event(db, **overrides) -> str:
    eid = str(uuid.uuid4())
    defaults = dict(
        event_id=eid,
        event_title="Test Event",
        event_type="military_escalation",
        stage_of_crisis="escalation",
        key_actors=["CountryA", "CountryB"],
        key_locations=["Location1"],
        driving_forces=["Force1"],
        major_risks=["Risk1"],
        current_balance="Balanced",
        event_confidence=0.8,
        region="Middle East",
        source_cluster_ids=[],
    )
    defaults.update(overrides)
    event = AbstractIRGEvent(**defaults)
    db.add(event)
    db.commit()
    return eid


def _create_run(db, event_id: str) -> str:
    rid = str(uuid.uuid4())
    run = PredictionRun(run_id=rid, event_id=event_id, status="complete", summary="Test run")
    db.add(run)
    db.commit()
    return rid


class TestRelationshipService:
    def test_rel_metadata_persisted(self, db):
        eid1 = _create_event(db, event_title="Event A")
        eid2 = _create_event(db, event_title="Event B")
        meta = {"shared_actors": ["CountryA"], "overlap_count": 3}
        rel = EventRelationship(
            from_event_id=min(eid1, eid2),
            to_event_id=max(eid1, eid2),
            relationship_type="shared_actor",
            weight=0.8,
            rel_metadata=meta,
        )
        db.add(rel)
        db.commit()

        fetched = db.query(EventRelationship).filter_by(
            from_event_id=min(eid1, eid2),
            to_event_id=max(eid1, eid2),
        ).first()
        assert fetched is not None
        assert fetched.rel_metadata == meta
        assert fetched.rel_metadata.get("shared_actors") == ["CountryA"]
        assert fetched.relationship_type == "shared_actor"

    def test_rel_metadata_not_lost_with_wrong_attr(self, db):
        eid1 = _create_event(db, event_title="Event C")
        eid2 = _create_event(db, event_title="Event D")
        meta = {"causal_direction": "A->B"}
        rel = EventRelationship(
            from_event_id=min(eid1, eid2),
            to_event_id=max(eid1, eid2),
            relationship_type="causal_chain",
            weight=0.6,
            rel_metadata=meta,
        )
        db.add(rel)
        db.commit()

        fetched = db.query(EventRelationship).filter_by(
            relationship_type="causal_chain"
        ).first()
        assert fetched is not None
        assert fetched.rel_metadata.get("causal_direction") == "A->B"

    def test_relationship_type_index(self, db, test_engine):
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("event_relationships")
        index_cols = [col for idx in indexes for col in idx["column_names"]]
        assert "relationship_type" in index_cols

    def test_composite_index_exists(self, db, test_engine):
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("event_relationships")
        found = any(
            "from_event_id" in idx["column_names"] and "to_event_id" in idx["column_names"]
            for idx in indexes
        )
        assert found, "Missing composite index on (from_event_id, to_event_id)"


class TestCalibrationService:
    def test_brier_score_calculation(self):
        from backend.services.calibration_service import compute_brier_score
        assert abs(compute_brier_score(1.0, 1.0) - 0.0) < 0.001
        assert abs(compute_brier_score(0.0, 0.0) - 0.0) < 0.001
        assert abs(compute_brier_score(1.0, 0.0) - 1.0) < 0.001
        assert abs(compute_brier_score(0.0, 1.0) - 1.0) < 0.001
        assert abs(compute_brier_score(0.5, 1.0) - 0.25) < 0.001
        assert abs(compute_brier_score(0.8, 1.0) - 0.04) < 0.001

    def test_calibration_grade_assignment(self):
        from backend.services.calibration_service import _compute_calibration_grade
        grade_a = _compute_calibration_grade(0.95, 0.95)
        assert grade_a["grade"] == "A"
        grade_f = _compute_calibration_grade(0.2, 0.2)
        assert grade_f["grade"] in ("E", "F")

    def test_get_calibration_summary_empty(self, db):
        from backend.services.calibration_service import compute_calibration_summary
        result = compute_calibration_summary(db)
        assert result["total_evaluations"] == 0
        assert result.get("calibration_grade") in ("N/A", None)

    def test_get_calibration_summary_with_data(self, db):
        from backend.services.calibration_service import compute_calibration_summary
        eid = _create_event(db)
        rid = _create_run(db, eid)
        sid = str(uuid.uuid4())
        script = ScenarioScript(
            script_id=sid, event_id=eid, run_id=rid,
            direction_type="escalation", script_title="Test Script",
            script_description="Desc", probability_low=0.1, probability_high=0.3,
            probability_central=0.2, confidence_level="medium",
        )
        db.add(script)
        db.commit()

        oid = str(uuid.uuid4())
        outcome = ActualOutcome(
            outcome_id=oid, event_id=eid, related_run_id=rid,
            actual_summary="Actual", actual_event_type="military_escalation",
        )
        db.add(outcome)
        db.commit()

        evid = str(uuid.uuid4())
        evaluation = PredictionEvaluation(
            evaluation_id=evid, run_id=rid, outcome_id=oid,
            script_hit=True, node_hit_rate=0.7,
            calibration_error=0.15, main_error_category="timing_error",
            detailed_error_analysis="Timing off",
        )
        db.add(evaluation)
        db.commit()

        result = compute_calibration_summary(db)
        assert result["total_evaluations"] >= 1
        assert 0 <= result["avg_brier_score"] <= 1
        assert result["calibration_grade"] in ("A", "B", "C", "D", "E", "F", "N/A")


class TestScenarioScriptEngine:
    def test_fallback_scenarios_structure(self, db):
        from backend.services.scenario_script_engine import _fallback_scenarios
        eid = _create_event(db)
        rid = _create_run(db, eid)
        event = db.query(AbstractIRGEvent).filter_by(event_id=eid).first()
        scripts = _fallback_scenarios(db, event, rid)
        assert len(scripts) == 3
        directions = {s["direction_type"] for s in scripts}
        assert "escalation" in directions
        assert "stalemate" in directions
        assert "de_escalation" in directions
        for s in scripts:
            assert "script_title" in s
            assert "probability_low" in s
            assert "probability_high" in s
            assert "probability_central" in s
            assert 0 <= s["probability_low"] <= 1
            assert s["probability_low"] <= s["probability_central"] <= s["probability_high"]

    def test_fallback_scenarios_probability_ranges(self, db):
        from backend.services.scenario_script_engine import _fallback_scenarios
        eid = _create_event(db)
        rid = _create_run(db, eid)
        event = db.query(AbstractIRGEvent).filter_by(event_id=eid).first()
        scripts = _fallback_scenarios(db, event, rid)
        for s in scripts:
            assert s["probability_low"] <= s["probability_central"]
            assert s["probability_central"] <= s["probability_high"]
            assert s["probability_high"] <= 1.0


class TestEventVersionService:
    def test_get_version_with_correct_params(self, db):
        from backend.services.event_version_service import create_version, get_version
        eid = _create_event(db)
        v1 = create_version(db, eid, "user1")
        assert v1 is not None
        assert v1["version_number"] == 1

        fetched = get_version(db, eid, 1)
        assert fetched is not None
        assert fetched["event_id"] == eid
        assert fetched["version_number"] == 1

    def test_get_version_not_found(self, db):
        from backend.services.event_version_service import get_version
        result = get_version(db, "nonexistent_id", 999)
        assert result is None


class TestAnalogyEngine:
    def test_key_lessons_empty_list_handled(self, db):
        from backend.services.analogy_engine import _rule_based_fallback
        eid = _create_event(db)
        event = db.query(AbstractIRGEvent).filter_by(event_id=eid).first()
        case = {
            "case_id": "test",
            "title": "Test Case",
            "event_type": "military_escalation",
            "region": "Middle East",
            "key_actors": ["A", "B"],
            "key_lessons": [],
            "outcome": "escalation",
            "similarity_score": 0.5,
        }
        result = _rule_based_fallback(event, [case])
        assert result is not None
        assert "matched_cases" in result
        if result["matched_cases"]:
            assert "analogy_implications_for_current" in result["matched_cases"][0]

    def test_key_lessons_missing_key_handled(self, db):
        from backend.services.analogy_engine import _rule_based_fallback
        eid = _create_event(db)
        event = db.query(AbstractIRGEvent).filter_by(event_id=eid).first()
        case = {
            "case_id": "test2",
            "title": "Test Case 2",
            "event_type": "diplomatic_negotiation",
            "region": "Asia",
            "key_actors": ["C", "D"],
            "outcome": "de_escalation",
            "similarity_score": 0.6,
        }
        result = _rule_based_fallback(event, [case])
        assert result is not None
        assert "is_fallback" in result


class TestDatabaseIndexes:
    def test_events_have_type_index(self, test_engine):
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("abstract_irg_events")
        indexed_cols = {col for idx in indexes for col in idx["column_names"]}
        assert "event_type" in indexed_cols
        assert "stage_of_crisis" in indexed_cols
        assert "region" in indexed_cols

    def test_events_composite_indexes(self, test_engine):
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("abstract_irg_events")
        found_type_stage = any(
            "event_type" in idx["column_names"] and "stage_of_crisis" in idx["column_names"]
            for idx in indexes
        )
        assert found_type_stage, "Missing composite index (event_type, stage_of_crisis)"

    def test_scripts_have_direction_index(self, test_engine):
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("scenario_scripts")
        indexed_cols = {col for idx in indexes for col in idx["column_names"]}
        assert "direction_type" in indexed_cols

    def test_raw_news_have_status_index(self, test_engine):
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("raw_news")
        indexed_cols = {col for idx in indexes for col in idx["column_names"]}
        assert "status" in indexed_cols

    def test_theory_have_name_index(self, test_engine):
        inspector = inspect(test_engine)
        indexes = inspector.get_indexes("theory_analyses")
        indexed_cols = {col for idx in indexes for col in idx["column_names"]}
        assert "theory_name" in indexed_cols
