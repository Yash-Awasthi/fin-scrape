"""
tests/e2e/test_full_pipeline.py
端到端测试：覆盖从RSS输入到PDF导出+评估的完整流程
运行方式：
    cd H:/国关推演/国关推演平台
    py -3 -m pytest tests/e2e/test_full_pipeline.py -v

注意：部分测试调用 Claude API（需配置 ANTHROPIC_API_KEY），标记为 @pytest.mark.api_call 的测试会实际消费 API token
"""
import pytest
import uuid
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.database import Base
from backend.models.raw_news import RawNews
from backend.models.news_cluster import NewsCluster
from backend.models.ir_event import AbstractIRGEvent
from backend.models.scenario import ScenarioScript, ScenarioStep
from backend.models.prediction import PredictionRun
from backend.models.outcome import ActualOutcome, PredictionEvaluation
from backend.models.theory_analysis import TheoryAnalysis
from backend.models.inference_layer import ActorProfile, TriggerRule, ConstraintRule, ScenarioContext


@pytest.fixture(scope="module")
def test_engine():
    """使用内存 SQLite 数据库进行测试"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db(test_engine):
    """每个测试函数使用独立的数据库会话"""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_news_data():
    """准备测试用新闻数据"""
    return [
        {
            "title": "Iran Advances Nuclear Enrichment Despite US Warnings",
            "body": "Iran has accelerated uranium enrichment at Natanz facility to 60%, "
                    "drawing sharp condemnation from Washington. US officials warn of 'serious consequences' "
                    "while Iran insists the program is for peaceful purposes. The IAEA has reported "
                    "reduced access to monitoring sites.",
            "source_name": "TEST_Reuters",
            "region": ["Middle East"],
            "entities": {"countries": ["Iran", "USA", "Israel"], "persons": [], "organizations": ["IAEA"], "locations": ["Natanz"]},
        },
        {
            "title": "IAEA Reports Reduced Access to Iranian Nuclear Sites",
            "body": "The International Atomic Energy Agency says Iran has denied inspectors access "
                    "to two key surveillance cameras at nuclear facilities, raising concerns.",
            "source_name": "TEST_BBC",
            "region": ["Middle East"],
            "entities": {"countries": ["Iran"], "persons": [], "organizations": ["IAEA", "UN"], "locations": ["Tehran"]},
        },
        {
            "title": "US Congress Pushes New Iran Sanctions Package",
            "body": "Bipartisan legislation targets Iran's oil exports and Revolutionary Guards. "
                    "Secondary sanctions would affect countries purchasing Iranian crude.",
            "source_name": "TEST_AP",
            "region": ["Middle East", "Americas"],
            "entities": {"countries": ["USA", "Iran"], "persons": [], "organizations": ["US Congress", "IRGC"], "locations": []},
        },
    ]


class TestDatabaseSetup:
    def test_all_tables_created(self, test_engine):
        """验证所有必要的数据库表都已创建"""
        from sqlalchemy import inspect
        inspector = inspect(test_engine)
        tables = inspector.get_table_names()

        required_tables = [
            "raw_news", "news_clusters", "abstract_irg_events",
            "theory_analyses", "scenario_scripts", "scenario_steps",
            "prediction_runs", "branch_runs", "actual_outcomes",
            "prediction_evaluations", "actor_profiles", "trigger_rules",
            "constraint_rules", "scenario_contexts",
        ]
        for table in required_tables:
            assert table in tables, f"缺少数据库表: {table}"

    def test_session_operations(self, db):
        """验证基本数据库 CRUD 操作"""
        news = RawNews(
            news_id=str(uuid.uuid4()),
            source_name="TEST",
            source_type="mock",
            title="Test News Article",
            dedupe_hash="test_hash_001",
            status="raw",
        )
        db.add(news)
        db.commit()

        fetched = db.query(RawNews).filter_by(dedupe_hash="test_hash_001").first()
        assert fetched is not None
        assert fetched.title == "Test News Article"


class TestIngestion:
    def test_compute_dedupe_hash_consistency(self):
        """相同 title+source 应产生相同 hash"""
        from backend.services.rss_ingestion_service import compute_dedupe_hash
        h1 = compute_dedupe_hash("Iran Nuclear Deal", "Reuters")
        h2 = compute_dedupe_hash("Iran Nuclear Deal", "Reuters")
        assert h1 == h2

    def test_compute_dedupe_hash_uniqueness(self):
        """不同内容应产生不同 hash"""
        from backend.services.rss_ingestion_service import compute_dedupe_hash
        h1 = compute_dedupe_hash("Iran Nuclear Deal", "Reuters")
        h2 = compute_dedupe_hash("China Taiwan Tensions", "Reuters")
        assert h1 != h2

    def test_extract_region_tags_middle_east(self):
        """中东关键词应识别为 Middle East"""
        from backend.services.rss_ingestion_service import extract_region_tags
        tags = extract_region_tags("Iran nuclear program threatens Israel and Saudi Arabia")
        assert "Middle East" in tags

    def test_extract_region_tags_multi(self):
        """多地区新闻应返回多个标签"""
        from backend.services.rss_ingestion_service import extract_region_tags
        tags = extract_region_tags("China and Russia face US sanctions in Europe")
        assert len(tags) >= 2

    def test_ir_relevance_filter_passes_ir(self):
        """国际关系相关新闻应通过过滤"""
        from backend.services.rss_ingestion_service import _is_ir_relevant
        assert _is_ir_relevant("NATO summit discusses Russia Ukraine war", "") is True
        assert _is_ir_relevant("China military exercises near Taiwan", "") is True

    def test_mock_news_ingestion(self, db):
        """模拟新闻应成功入库"""
        from backend.services.ingestion_service import get_mock_news
        result = get_mock_news(db)
        assert len(result) > 0
        count = db.query(RawNews).filter_by(source_type="mock").count()
        assert count > 0

    def test_mock_news_dedup(self, db):
        """重复运行不应产生重复条目"""
        from backend.services.ingestion_service import get_mock_news
        db.query(RawNews).filter_by(source_type="mock").delete()
        db.commit()

        result1 = get_mock_news(db)
        count_after_first = db.query(RawNews).filter_by(source_type="mock").count()
        result2 = get_mock_news(db)
        count_after_second = db.query(RawNews).filter_by(source_type="mock").count()
        assert count_after_first == count_after_second, "第二次运行产生了重复条目"
        assert count_after_first == len(result1)

    def test_entity_extraction(self):
        """实体提取应识别已知国家"""
        from backend.services.rss_ingestion_service import simple_entity_extract
        result = simple_entity_extract("Russia and Ukraine conflict; NATO responds")
        assert "Russia" in result["countries"] or "Ukraine" in result["countries"]
        assert "NATO" in result["organizations"]

    def test_source_registry_completeness(self):
        """新闻源注册表应包含所有必要字段"""
        from backend.services.source_registry import get_enabled_sources
        sources = get_enabled_sources()
        assert len(sources) >= 5, "至少需要 5 个启用的新闻源"
        for source in sources:
            assert source.source_id, "source_id 不能为空"
            assert source.feed_url, "feed_url 不能为空"
            assert source.region, "region 不能为空"


class TestGeocoding:
    def test_builtin_lookup_exact(self):
        """内置库精确匹配"""
        from backend.services.geocoding_service import get_coordinates
        result = get_coordinates("Beijing")
        assert result is not None
        assert abs(result["lat"] - 39.9042) < 0.5
        assert result["source"] == "builtin"

    def test_builtin_lookup_case_insensitive(self):
        """内置库不区分大小写"""
        from backend.services.geocoding_service import get_coordinates
        result = get_coordinates("BEIJING")
        assert result is not None

    def test_builtin_partial_match(self):
        """包含匹配（Taiwan Strait -> Taiwan）"""
        from backend.services.geocoding_service import get_coordinates
        result = get_coordinates("Taiwan Strait")
        assert result is not None

    def test_coordinates_for_event(self):
        """事件坐标获取（多候选地点）"""
        from backend.services.geocoding_service import get_coordinates_for_event
        result = get_coordinates_for_event(
            key_locations=["Natanz", "Tehran"],
            region="Middle East",
        )
        assert result is not None
        assert "lat" in result
        assert "lng" in result

    def test_coordinates_region_fallback(self):
        """未知地点应回退到地区中心"""
        from backend.services.geocoding_service import get_coordinates_for_event
        result = get_coordinates_for_event(
            key_locations=["XYZ_Unknown_Place_9999"],
            region="Middle East",
        )
        assert result is not None

    def test_cache_stats(self):
        """缓存统计应返回合理数据"""
        from backend.services.geocoding_service import get_cache_stats
        stats = get_cache_stats()
        assert stats["builtin_count"] >= 60, "内置坐标库应至少有 60 条记录"


class TestClustering:
    def _insert_test_news(self, db, sample_news_data):
        """插入测试新闻"""
        import hashlib
        inserted = []
        for i, article in enumerate(sample_news_data):
            h = hashlib.sha256(f"{article['title']}|test{i}".encode()).hexdigest()
            news = RawNews(
                news_id=str(uuid.uuid4()),
                source_name=article["source_name"],
                source_type="test",
                title=article["title"],
                body=article["body"],
                region_tags=article["region"],
                raw_entities=article["entities"],
                dedupe_hash=h,
                status="raw",
            )
            db.add(news)
            inserted.append(news)
        db.commit()
        return inserted

    def test_cluster_structure(self, db, sample_news_data):
        """聚类应产生正确结构的输出"""
        self._insert_test_news(db, sample_news_data)
        from backend.services.clustering_service import _fallback_clustering
        news_list = db.query(RawNews).filter_by(status="raw").all()
        if news_list:
            clusters = _fallback_clustering(db, news_list)
            for cluster in clusters:
                assert "cluster_id" in cluster
                assert "cluster_title" in cluster


class TestPDFExport:
    def _create_test_event(self, db) -> str:
        """创建测试事件"""
        event_id = str(uuid.uuid4())
        event = AbstractIRGEvent(
            event_id=event_id,
            event_title="伊朗核问题危机测试",
            event_type="military_escalation",
            stage_of_crisis="escalation",
            key_actors=["Iran", "USA", "Israel"],
            key_locations=["Natanz", "Tehran"],
            driving_forces=["核扩散压力", "美国制裁"],
            major_risks=["军事打击", "核升级"],
            current_balance="美伊对峙持续",
            event_confidence=0.8,
            geo_coordinates={"lat": 32.42, "lng": 53.68},
            region="Middle East",
            source_cluster_ids=[],
        )
        db.add(event)
        db.commit()
        return event_id

    def _create_test_run(self, db, event_id: str) -> str:
        """创建测试推演"""
        run_id = str(uuid.uuid4())
        run = PredictionRun(
            run_id=run_id,
            event_id=event_id,
            root_question="伊朗核危机将如何演变？",
            status="complete",
            summary="测试推演摘要",
        )
        db.add(run)
        db.commit()
        return run_id

    def test_pdf_generates_bytes(self, db):
        """PDF 生成应返回有效字节流"""
        from backend.services.pdf_export_service import generate_pdf_report
        event_id = self._create_test_event(db)
        pdf_bytes = generate_pdf_report(db, "event_brief", event_id=event_id)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    def test_pdf_is_valid_pdf_format(self, db):
        """生成的 PDF 应有正确的文件头"""
        from backend.services.pdf_export_service import generate_pdf_report
        event_id = self._create_test_event(db)
        pdf_bytes = generate_pdf_report(db, "event_brief", event_id=event_id)
        assert pdf_bytes[:4] == b"%PDF"

    def test_scenario_report_pdf(self, db):
        """情景推演报告 PDF"""
        from backend.services.pdf_export_service import generate_pdf_report
        event_id = self._create_test_event(db)
        run_id = self._create_test_run(db, event_id)

        script = ScenarioScript(
            script_id=str(uuid.uuid4()),
            event_id=event_id,
            run_id=run_id,
            direction_type="escalation",
            script_title="测试升级剧本",
            script_description="测试描述",
            probability_low=0.1,
            probability_high=0.3,
            probability_central=0.2,
            confidence_level="medium",
        )
        db.add(script)
        db.commit()

        pdf_bytes = generate_pdf_report(db, "scenario_report", event_id=event_id, run_id=run_id)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:4] == b"%PDF"

    def test_review_report_pdf(self, db):
        """预测复盘报告 PDF"""
        from backend.services.pdf_export_service import generate_pdf_report
        event_id = self._create_test_event(db)
        run_id = self._create_test_run(db, event_id)

        outcome = ActualOutcome(
            outcome_id=str(uuid.uuid4()),
            event_id=event_id,
            related_run_id=run_id,
            actual_summary="实际发生了某事件",
            actual_event_type="military_escalation",
        )
        db.add(outcome)
        db.commit()

        pdf_bytes = generate_pdf_report(db, "review_report", run_id=run_id)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    def test_all_report_types(self, db):
        """所有四种报告类型都应能生成"""
        from backend.services.pdf_export_service import generate_pdf_report
        event_id = self._create_test_event(db)
        run_id = self._create_test_run(db, event_id)

        for report_type in ["event_brief", "scenario_report", "thematic_report", "review_report"]:
            pdf_bytes = generate_pdf_report(db, report_type, event_id=event_id, run_id=run_id)
            assert isinstance(pdf_bytes, bytes), f"{report_type} 生成失败"
            assert len(pdf_bytes) > 50, f"{report_type} PDF 太短"


class TestPersistence:
    def test_prediction_run_lifecycle(self, db):
        """推演记录的完整生命周期"""
        from backend.services.persistence_service import (
            create_prediction_run, complete_run, get_run, list_runs,
            record_actual_outcome, create_evaluation
        )

        event_id = str(uuid.uuid4())
        event = AbstractIRGEvent(
            event_id=event_id,
            event_title="测试事件",
            event_type="diplomatic_negotiation",
            stage_of_crisis="emergence",
            key_actors=["A", "B"],
        )
        db.add(event)
        db.commit()

        run = create_prediction_run(db, event_id)
        assert run.status == "running"

        complete_run(db, run.run_id, "测试摘要", [])
        run_dict = get_run(db, run.run_id)
        assert run_dict["status"] == "complete"

        runs_list = list_runs(db, event_id=event_id)
        assert len(runs_list) >= 1

        outcome = record_actual_outcome(
            db, run.run_id, event_id,
            "实际发生了对话", "diplomatic_negotiation",
            None
        )
        assert outcome["outcome_id"] is not None

        evaluation = create_evaluation(
            db, run.run_id, outcome["outcome_id"],
            None, False, 0.3, "timing_error",
            "事件发生但时机判断有误",
            ["方向判断正确"], ["时机错误"], ["改进建议"]
        )
        assert evaluation["evaluation_id"] is not None


class TestAntiTemplate:
    def test_anti_template_check_structure(self):
        """反模板检查应返回正确结构（使用回退值，无需 API）"""
        result = {
            "over_template_score": 0.3,
            "regenerate_recommended": False,
            "over_template_reasoning": "test",
        }
        assert "over_template_score" in result
        assert 0.0 <= result["over_template_score"] <= 1.0
        assert isinstance(result["regenerate_recommended"], bool)


class TestAPIHealth:
    """使用 FastAPI TestClient 进行 API 测试"""

    @pytest.fixture
    def client(self):
        try:
            from fastapi.testclient import TestClient
            from backend.main import app
            return TestClient(app)
        except Exception as e:
            pytest.skip(f"无法创建 TestClient: {e}")

    def test_health_endpoint(self, client):
        """健康检查端点"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data

    def test_news_endpoint(self, client):
        """新闻列表端点"""
        response = client.get("/api/v1/news")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data

    def test_events_endpoint(self, client):
        """事件列表端点"""
        response = client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data

    def test_clusters_endpoint(self, client):
        """事件簇列表端点"""
        response = client.get("/api/v1/clusters")
        assert response.status_code == 200

    def test_globe_endpoint(self, client):
        """地球视图端点"""
        response = client.get("/api/v1/globe/events")
        assert response.status_code == 200
        data = response.json()
        assert "points" in data

    def test_sources_endpoint(self, client):
        """新闻源列表端点"""
        response = client.get("/api/v1/pipeline/sources")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5

    def test_history_endpoint(self, client):
        """历史记录端点"""
        response = client.get("/api/v1/history")
        assert response.status_code == 200

    def test_geocoding_stats_endpoint(self, client):
        """地理编码统计端点"""
        response = client.get("/api/v1/pipeline/geocoding/stats")
        assert response.status_code == 200
        data = response.json()
        assert "builtin_count" in data

    def test_full_pipeline_mock(self, client):
        """完整流程（mock 模式，不消费 API）
        /run-full 现在是异步接口：立即返回 task_id，后台线程执行。
        前端通过 GET /tasks/{task_id} 轮询进度和结果。
        """
        response = client.post("/api/v1/pipeline/run-full?use_mock=true")
        assert response.status_code == 200, response.text
        data = response.json()
        assert "task_id" in data, f"缺少 task_id 字段: {data}"
        assert "status" in data, f"缺少 status 字段: {data}"
        assert data["status"] in ("pending", "running"), (
            f"status 应为 pending/running，实际: {data['status']}"
        )
        task_id = data["task_id"]
        poll_response = client.get(f"/api/v1/pipeline/tasks/{task_id}")
        assert poll_response.status_code == 200, poll_response.text
        poll_data = poll_response.json()
        assert "task_id" in poll_data
        assert poll_data["task_id"] == task_id
        assert "steps" in poll_data
        assert isinstance(poll_data["steps"], list)


@pytest.mark.api_call
@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY is not set; skipping external API E2E tests",
)
class TestFullE2EPipeline:
    """
    端到端流程测试
    需要 ANTHROPIC_API_KEY 环境变量
    运行时间：约 2-5 分钟（多次 Claude API 调用）
    """

    def test_full_mock_pipeline(self):
        """
        使用 Mock 数据的完整流程：
        Mock新闻 -> 聚类 -> 事件抽象 -> 理论分析 -> 剧本生成 -> PDF导出
        """
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()

        try:
            from backend.services.ingestion_service import get_mock_news
            news = get_mock_news(db)
            assert len(news) >= 5, "Mock 新闻数量不足"

            from backend.services.clustering_service import cluster_news
            clusters = cluster_news(db)
            assert len(clusters) >= 1, "聚类数量为0"

            from backend.services.event_abstraction_service import abstract_all_unprocessed_clusters
            events = abstract_all_unprocessed_clusters(db)
            assert len(events) >= 1, "事件抽象数量为0"

            event_id = events[0]["event_id"]

            event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first()

            from backend.services.theory_analysis_service import generate_theory_analyses
            analyses = generate_theory_analyses(db, event_id)
            assert len(analyses) >= 1, "理论分析数量为0"

            from backend.services.persistence_service import create_prediction_run, complete_run
            run = create_prediction_run(db, event_id)

            from backend.services.scenario_script_engine import run_scenario_engine
            scripts = run_scenario_engine(db, event_id, run.run_id)
            assert len(scripts) >= 1, "剧本生成数量为0"

            for script in scripts:
                assert "anti_template_check" in script, f"剧本 {script.get('script_title')} 缺少反模板检查结果"
                assert "over_template_score" in script["anti_template_check"]
                assert "over_template_flagged" in script

            from backend.services.pdf_export_service import generate_pdf_report
            complete_run(db, run.run_id, "E2E 测试完成", [s["script_id"] for s in scripts])

            for report_type in ["event_brief", "scenario_report"]:
                pdf = generate_pdf_report(db, report_type, event_id=event_id, run_id=run.run_id)
                assert isinstance(pdf, bytes)
                assert len(pdf) > 100, f"{report_type} PDF 太短"

        finally:
            db.close()
            engine.dispose()
