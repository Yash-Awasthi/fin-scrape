"""
tests/test_integration.py
综合集成测试 — 验证跨模块数据流、状态一致性和 API 端到端正确性
不依赖外部 Claude API（使用 SQLite 内存数据，Mock 数据注入）
"""
import pytest
import uuid
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-fake-key-for-testing")
    os.environ.setdefault("DEBUG", "true")
    from backend.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(scope="module")
def seeded_event(client):
    from backend.db.database import SessionLocal
    from backend.models.ir_event import AbstractIRGEvent, EventType, CrisisStage

    db = SessionLocal()
    try:
        event = AbstractIRGEvent(
            event_id=str(uuid.uuid4()),
            event_title="集成测试事件：台海局势",
            event_type=EventType.military_escalation,
            stage_of_crisis=CrisisStage.escalation,
            key_actors=["中国", "美国", "台湾"],
            actor_roles={"中国": "主要行动方", "美国": "介入方"},
            key_locations=["台湾海峡"],
            strategic_dimensions=["军事威慑", "外交施压"],
            driving_forces=["两岸紧张局势上升"],
            constraints=["核威慑限制"],
            immediate_triggers=["军演宣布"],
            current_balance="中美博弈",
            major_risks=["军事误判"],
            current_opportunities=["外交对话"],
            event_confidence=0.85,
            is_fallback=False,
            geo_coordinates={"lat": 23.5, "lng": 121.0},
            region="东亚",
            source_cluster_ids=[],
            status="active",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        event_id = event.event_id
    finally:
        db.close()

    yield event_id

    db2 = SessionLocal()
    try:
        from backend.models.annotation import Annotation
        from backend.models.theory_analysis import TheoryAnalysis
        db2.query(Annotation).filter_by(entity_id=event_id).delete()
        db2.query(TheoryAnalysis).filter_by(event_id=event_id).delete()
        db2.query(AbstractIRGEvent).filter_by(event_id=event_id).delete()
        db2.commit()
    finally:
        db2.close()


class TestHealthCheck:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data

    def test_health_has_deps_info(self, client):
        resp = client.get("/api/v1/health")
        deps = resp.json().get("deps", {})
        assert "local_proxy_7897" in deps
        assert "claude_api_relay" in deps


class TestEventConsistency:
    def test_list_events_returns_200(self, client):
        resp = client.get("/api/v1/events")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert isinstance(body["items"], list)

    def test_seeded_event_visible_in_list(self, client, seeded_event):
        resp = client.get("/api/v1/events")
        assert resp.status_code == 200
        ids = [e["event_id"] for e in resp.json()["items"]]
        assert seeded_event in ids

    def test_get_event_detail(self, client, seeded_event):
        resp = client.get(f"/api/v1/events/{seeded_event}")
        assert resp.status_code == 200
        ev = resp.json()
        assert ev["event_id"] == seeded_event
        assert ev["event_title"] == "集成测试事件：台海局势"
        assert ev["event_type"] == "military_escalation"
        assert ev["stage_of_crisis"] == "escalation"
        assert ev["region"] == "东亚"
        assert isinstance(ev["key_actors"], list)
        assert len(ev["key_actors"]) == 3

    def test_get_nonexistent_event_404(self, client):
        resp = client.get(f"/api/v1/events/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_event_confidence_in_range(self, client, seeded_event):
        ev = client.get(f"/api/v1/events/{seeded_event}").json()
        conf = ev["event_confidence"]
        assert 0.0 <= conf <= 1.0


class TestGlobeModule:
    def test_globe_events_returns_200(self, client):
        resp = client.get("/api/v1/globe/events")
        assert resp.status_code == 200
        body = resp.json()
        assert "points" in body
        assert "total" in body

    def test_seeded_event_in_globe_points(self, client, seeded_event):
        resp = client.get("/api/v1/globe/events")
        assert resp.status_code == 200
        event_ids = [p["event_id"] for p in resp.json()["points"]]
        assert seeded_event in event_ids

    def test_globe_point_has_required_fields(self, client, seeded_event):
        points = client.get("/api/v1/globe/events").json()["points"]
        pt = next((p for p in points if p["event_id"] == seeded_event), None)
        assert pt is not None
        for field in ("event_id", "event_title", "event_type", "lat", "lng", "region"):
            assert field in pt
        assert -90 <= pt["lat"] <= 90
        assert -180 <= pt["lng"] <= 180

    def test_globe_response_has_relationships_field(self, client):
        body = client.get("/api/v1/globe/events").json()
        assert "relationships" in body
        assert isinstance(body["relationships"], list)

    def test_globe_point_has_scenario_summary(self, client, seeded_event):
        points = client.get("/api/v1/globe/events").json()["points"]
        pt = next((p for p in points if p["event_id"] == seeded_event), None)
        assert pt is not None
        assert "scenario_summary" in pt
        ss = pt["scenario_summary"]
        assert "has_scenarios" in ss
        assert "script_count" in ss

    def test_globe_relationships_structure(self, client):
        body = client.get("/api/v1/globe/events").json()
        for rel in body["relationships"]:
            assert "from" in rel
            assert "to" in rel
            assert rel["type"] in ("shared_actor", "same_region")
            assert isinstance(rel["actors"], list)
            assert isinstance(rel["weight"], int)


class TestTheoryModule:
    def test_theory_endpoint_returns_200(self, client, seeded_event):
        resp = client.get(f"/api/v1/events/{seeded_event}/theories")
        assert resp.status_code == 200
        body = resp.json()
        assert body["event_id"] == seeded_event
        assert "analyses" in body
        assert isinstance(body["analyses"], list)

    def test_theory_empty_for_new_event(self, client, seeded_event):
        resp = client.get(f"/api/v1/events/{seeded_event}/theories")
        assert resp.json()["analyses"] == []

    def test_theory_endpoint_for_unknown_event(self, client):
        resp = client.get(f"/api/v1/events/{uuid.uuid4()}/theories")
        assert resp.status_code in (200, 404)


class TestScenarioModule:
    def test_scripts_endpoint_returns_200(self, client, seeded_event):
        resp = client.get(f"/api/v1/events/{seeded_event}/scripts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["event_id"] == seeded_event
        assert "scripts" in body
        assert isinstance(body["scripts"], list)

    def test_scripts_empty_for_new_event(self, client, seeded_event):
        resp = client.get(f"/api/v1/events/{seeded_event}/scripts")
        assert resp.json()["scripts"] == []


class TestAnnotationModule:
    def test_create_annotation(self, client, seeded_event):
        payload = {
            "entity_type": "event",
            "entity_id": seeded_event,
            "content": "这是一条集成测试批注",
            "tags": ["insight", "test"],
            "importance": "high",
        }
        resp = client.post("/api/v1/annotations", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["annotation_id"]
        assert body["entity_type"] == "event"
        assert body["entity_id"] == seeded_event
        assert body["content"] == "这是一条集成测试批注"
        assert body["importance"] == "high"
        assert body["version"] == "1"

    def test_list_annotations_for_entity(self, client, seeded_event):
        resp = client.get("/api/v1/annotations", params={"entity_type": "event", "entity_id": seeded_event})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert any(a["entity_id"] == seeded_event for a in body["items"])

    def test_get_entity_annotations_shortcut(self, client, seeded_event):
        resp = client.get(f"/api/v1/annotations/entity/event/{seeded_event}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["entity_type"] == "event"
        assert body["entity_id"] == seeded_event
        assert body["total"] >= 1

    def test_update_annotation_increments_version(self, client, seeded_event):
        create_resp = client.post("/api/v1/annotations", json={
            "entity_type": "event",
            "entity_id": seeded_event,
            "content": "原始内容",
            "importance": "medium",
        })
        ann_id = create_resp.json()["annotation_id"]

        upd_resp = client.patch(f"/api/v1/annotations/{ann_id}", json={
            "content": "更新后内容",
            "importance": "high",
        })
        assert upd_resp.status_code == 200
        upd = upd_resp.json()
        assert upd["content"] == "更新后内容"
        assert upd["importance"] == "high"
        assert upd["version"] == "2"
        assert upd["history_count"] == 1

    def test_get_annotation_with_history(self, client, seeded_event):
        ann_id = client.post("/api/v1/annotations", json={
            "entity_type": "event", "entity_id": seeded_event, "content": "v1",
        }).json()["annotation_id"]
        client.patch(f"/api/v1/annotations/{ann_id}", json={"content": "v2"})

        detail = client.get(f"/api/v1/annotations/{ann_id}").json()
        assert detail["version"] == "2"
        assert "history" in detail
        assert len(detail["history"]) == 1
        assert detail["history"][0]["version"] == "1"
        assert detail["history"][0]["content"] == "v1"

    def test_delete_annotation(self, client, seeded_event):
        ann_id = client.post("/api/v1/annotations", json={
            "entity_type": "event", "entity_id": seeded_event, "content": "待删除",
        }).json()["annotation_id"]

        del_resp = client.delete(f"/api/v1/annotations/{ann_id}")
        assert del_resp.status_code == 200
        assert del_resp.json()["status"] == "deleted"

        get_resp = client.get(f"/api/v1/annotations/{ann_id}")
        assert get_resp.status_code == 404

    def test_annotation_invalid_entity_type(self, client):
        resp = client.post("/api/v1/annotations", json={
            "entity_type": "invalid_type",
            "entity_id": "any-id",
            "content": "测试",
        })
        assert resp.status_code == 400

    def test_annotation_supports_all_entity_types(self, client, seeded_event):
        for entity_type in ("event", "script", "theory", "analogy", "run"):
            resp = client.post("/api/v1/annotations", json={
                "entity_type": entity_type,
                "entity_id": seeded_event,
                "content": f"测试 {entity_type} 批注",
            })
            assert resp.status_code == 200, f"entity_type={entity_type} 应成功创建批注"


class TestPipelineRoutes:
    def test_list_sources(self, client):
        resp = client.get("/api/v1/pipeline/sources")
        assert resp.status_code == 200
        body = resp.json()
        assert "sources" in body
        assert "total" in body
        assert isinstance(body["sources"], list)

    def test_get_nonexistent_task_404(self, client):
        resp = client.get(f"/api/v1/pipeline/tasks/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_reset_endpoint_returns_confirmation_required(self, client):
        resp = client.post("/api/v1/pipeline/reset")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "confirmation_required"
        assert "confirm_token" in body


class TestAnalogyModule:
    def test_analogies_endpoint_for_new_event(self, client, seeded_event):
        resp = client.get(f"/api/v1/events/{seeded_event}/analogies")
        assert resp.status_code in (200, 404)

    def test_cases_list_returns_200(self, client):
        resp = client.get("/api/v1/analogies/cases")
        assert resp.status_code == 200
        body = resp.json()
        assert "cases" in body
        assert "total" in body


class TestCrossModuleDataFlow:
    def test_event_visible_in_globe_after_creation(self, client):
        from backend.db.database import SessionLocal
        from backend.models.ir_event import AbstractIRGEvent, EventType, CrisisStage

        new_id = str(uuid.uuid4())
        db = SessionLocal()
        try:
            ev = AbstractIRGEvent(
                event_id=new_id,
                event_title="跨模块测试事件",
                event_type=EventType.diplomatic_negotiation,
                stage_of_crisis=CrisisStage.emergence,
                key_actors=["测试国A"],
                actor_roles={},
                key_locations=["测试地区"],
                strategic_dimensions=[],
                driving_forces=[],
                constraints=[],
                immediate_triggers=[],
                current_balance="",
                major_risks=[],
                current_opportunities=[],
                event_confidence=0.7,
                geo_coordinates={"lat": 35.0, "lng": 105.0},
                region="亚洲",
                source_cluster_ids=[],
                status="active",
            )
            db.add(ev)
            db.commit()
        finally:
            db.close()

        try:
            events_resp = client.get("/api/v1/events")
            assert any(e["event_id"] == new_id for e in events_resp.json()["items"])

            globe_resp = client.get("/api/v1/globe/events")
            globe_ids = [p["event_id"] for p in globe_resp.json()["points"]]
            assert new_id in globe_ids

            theory_resp = client.get(f"/api/v1/events/{new_id}/theories")
            assert theory_resp.status_code == 200

            script_resp = client.get(f"/api/v1/events/{new_id}/scripts")
            assert script_resp.status_code == 200

        finally:
            db3 = SessionLocal()
            try:
                db3.query(AbstractIRGEvent).filter_by(event_id=new_id).delete()
                db3.commit()
            finally:
                db3.close()

    def test_annotation_count_consistent_after_updates(self, client, seeded_event):
        initial = client.get(
            "/api/v1/annotations/entity/event/" + seeded_event
        ).json()["total"]

        for i in range(3):
            client.post("/api/v1/annotations", json={
                "entity_type": "event",
                "entity_id": seeded_event,
                "content": f"一致性测试批注 {i}",
            })

        resp = client.get("/api/v1/annotations/entity/event/" + seeded_event)
        body = resp.json()
        assert body["total"] == initial + 3
        assert len(body["items"]) == body["total"]


class TestCalibrationModule:
    def test_calibration_summary(self, client):
        resp = client.get("/api/v1/calibration/summary")
        assert resp.status_code == 200

    def test_calibration_theories(self, client):
        resp = client.get("/api/v1/calibration/theories")
        assert resp.status_code == 200

    def test_calibration_directions(self, client):
        resp = client.get("/api/v1/calibration/directions")
        assert resp.status_code == 200
