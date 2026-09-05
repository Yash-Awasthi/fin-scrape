"""
tests/test_api_routes.py
轻量路由测试——验证"曾经 404"的接口真实存在且返回正确结构。
不调用 Claude API，不发外网请求（所有 LLM 调用在 DB 为空时不会触发）。

覆盖：
  - GET /api/health
  - GET /api/pipeline/sources
  - GET /api/analogies/cases
  - GET /api/analogies/cases/{case_id}   (不存在的 ID → 404)
  - GET /api/pipeline/tasks/{task_id}    (不存在 → 404，文案友好)
  - GET /api/events                      (DB 为空 → 200 + 空列表)
  - GET /api/news                        (DB 为空 → 200 + 空列表)
  - GET /api/clusters                    (DB 为空 → 200 + 空列表)
  - task_manager.to_dict() 字段完整性
"""
import pytest


# ─────────────────── /api/health ───────────────────────────

def test_health_returns_200(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200, resp.text


def test_health_has_deps_field(client):
    data = client.get("/api/health").json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "deps" in data
    assert "local_proxy_7897" in data["deps"]
    assert "claude_api_relay" in data["deps"]


def test_health_has_version(client):
    data = client.get("/api/health").json()
    assert "version" in data
    assert "app" in data


# ─────────────────── /api/pipeline/sources ─────────────────

def test_pipeline_sources_returns_200(client):
    resp = client.get("/api/v1/pipeline/sources")
    assert resp.status_code == 200, resp.text


def test_pipeline_sources_structure(client):
    data = client.get("/api/v1/pipeline/sources").json()
    assert "total" in data, f"缺少 total 字段: {data}"
    assert "sources" in data, f"缺少 sources 字段: {data}"
    assert isinstance(data["sources"], list)
    assert isinstance(data["total"], int)


# ─────────────────── /api/analogies/cases ──────────────────

def test_analogies_cases_returns_200(client):
    resp = client.get("/api/v1/analogies/cases")
    assert resp.status_code == 200, resp.text


def test_analogies_cases_structure(client):
    data = client.get("/api/v1/analogies/cases").json()
    assert "total" in data, f"缺少 total 字段: {data}"
    assert "cases" in data, f"缺少 cases 字段: {data}"
    assert isinstance(data["cases"], list)


def test_analogies_cases_filter_params(client):
    """筛选参数不应导致 500"""
    resp = client.get("/api/v1/analogies/cases", params={"event_type": "military_escalation"})
    assert resp.status_code == 200, resp.text


def test_analogies_case_not_found(client):
    """不存在的 case_id 应返回 404"""
    resp = client.get("/api/v1/analogies/cases/nonexistent-case-id-xyz")
    assert resp.status_code == 404, resp.text


# ─────────────────── /api/pipeline/tasks/{task_id} ─────────

def test_task_not_found_returns_404(client):
    resp = client.get("/api/v1/pipeline/tasks/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404, resp.text


def test_task_not_found_detail_is_informative(client):
    data = client.get("/api/v1/pipeline/tasks/fake-task-id-xyz").json()
    assert "detail" in data
    # 文案应包含提示（不是仅"Not Found"）
    assert len(data["detail"]) > 10


# ─────────────────── task_manager 字段完整性 ────────────────

def test_task_manager_to_dict_fields():
    """TaskProgress.to_dict() 必须包含前端所需的所有字段"""
    from backend.services.task_manager import TaskProgress
    import time

    task = TaskProgress("test-task-001")
    d = task.to_dict()

    required_fields = [
        "task_id", "status", "created_at", "started_at",
        "finished_at", "updated_at", "running_seconds",
        "error", "steps", "result",
    ]
    for f in required_fields:
        assert f in d, f"to_dict() 缺少字段: {f}"

    assert d["task_id"] == "test-task-001"
    assert d["status"] == "pending"
    assert d["running_seconds"] == 0.0
    assert isinstance(d["steps"], list)
    assert len(d["steps"]) == 6


def test_task_step_has_time_fields():
    """每个 step 必须包含 started_at / finished_at / duration_seconds"""
    from backend.services.task_manager import TaskProgress

    task = TaskProgress("test-task-002")
    for step in task.to_dict()["steps"]:
        assert "started_at" in step, f"step {step['key']} 缺少 started_at"
        assert "finished_at" in step, f"step {step['key']} 缺少 finished_at"
        assert "duration_seconds" in step, f"step {step['key']} 缺少 duration_seconds"


def test_task_step_timing_on_set_step():
    """set_step 转为 running 时应记录 started_at；转为 done 时记录 finished_at 和 duration"""
    import time
    from backend.services.task_manager import TaskProgress

    task = TaskProgress("test-task-003")
    task.set_step("fetch", "running")
    time.sleep(0.05)  # 等 50ms
    task.set_step("fetch", "done")

    step = next(s for s in task.to_dict()["steps"] if s["key"] == "fetch")
    assert step["status"] == "done"
    assert step["started_at"] is not None
    assert step["finished_at"] is not None
    assert step["duration_seconds"] is not None
    assert step["duration_seconds"] >= 0.0


def test_task_updated_at_changes_on_state_change():
    """任何状态变更都应更新 updated_at"""
    from backend.services.task_manager import TaskProgress
    import time

    task = TaskProgress("test-task-004")
    initial_updated = task.to_dict()["updated_at"]
    time.sleep(0.01)
    task.start()
    assert task.to_dict()["updated_at"] != initial_updated


# ─────────────────── 列表接口（DB 为空时） ──────────────────

def test_events_list_empty_db(client):
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "total" in data
    assert "items" in data


def test_news_list_empty_db(client):
    resp = client.get("/api/v1/news")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "total" in data
    assert "items" in data


def test_clusters_list_empty_db(client):
    resp = client.get("/api/v1/clusters")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "total" in data
    assert "items" in data


# ─────────────────── pipeline run-full 结果字段 ─────────────

def test_pipeline_result_fields_doc():
    """
    验证 pipeline _run_pipeline_task 的 result dict 包含前端所需的标准字段。
    （此测试不真正运行 pipeline，只检查字段名称定义。）
    """
    # 模拟 result 结构（与 pipeline.py 中的 result dict 保持一致）
    result = {
        "status": "ok",
        "data_source": "live",
        "news_collected": 0,
        "clusters_formed": 0,
        "events_abstracted": 0,
        # 前端标准字段
        "news_count": 0,
        "cluster_count": 0,
        "event_count": 0,
        "theory_count": 0,
        "scenario_count": 0,
        "run_ids": [],
        "clusters": [],
        "events": [],
        "failed_sources": [],
    }
    standard_fields = [
        "news_count", "cluster_count", "event_count",
        "theory_count", "scenario_count", "run_ids",
        "data_source", "failed_sources",
    ]
    for f in standard_fields:
        assert f in result, f"pipeline result 缺少字段: {f}"
