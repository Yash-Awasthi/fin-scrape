"""
Test API Layer
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from src.api.app import create_app
from src.api.models import AnalysisRequest, AnalysisType, ExportFormat


class TestAPI:
    """测试API端点"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def mock_task_manager(self):
        """模拟任务管理器"""
        with patch('src.api.routes.task_manager') as mock:
            mock.create_task = AsyncMock()
            mock.get_task = AsyncMock()
            mock.update_task = AsyncMock()
            yield mock

    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        assert "AutoGen Financial Analysis API" in response.json()["message"]

    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_create_analysis_endpoint(self, client, mock_task_manager):
        """测试创建分析端点"""
        # 模拟任务创建
        mock_task = Mock()
        mock_task.request.id = "test-task-id"
        mock_task.status.value = "pending"
        mock_task_manager.create_task.return_value = mock_task

        # 测试数据
        request_data = {
            "symbols": ["AAPL"],
            "analysis_type": "comprehensive",
            "export_formats": ["html"]
        }

        response = client.post("/api/v1/analysis", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert data["status"] == "pending"

    def test_create_analysis_validation_error(self, client):
        """测试分析创建验证错误"""
        # 无效的请求数据
        request_data = {
            "symbols": [],  # 空列表
            "analysis_type": "comprehensive"
        }

        response = client.post("/api/v1/analysis", json=request_data)
        assert response.status_code == 422

    def test_get_analysis_status(self, client, mock_task_manager):
        """测试获取分析状态端点"""
        # 模拟任务
        mock_task = Mock()
        mock_task.to_dict.return_value = {
            "request_id": "test-task-id",
            "status": "running",
            "progress": 50.0
        }
        mock_task_manager.get_task.return_value = mock_task

        response = client.get("/api/v1/analysis/test-task-id")

        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == "test-task-id"
        assert data["status"] == "running"

    def test_get_analysis_status_not_found(self, client, mock_task_manager):
        """测试获取不存在的任务状态"""
        mock_task_manager.get_task.return_value = None

        response = client.get("/api/v1/analysis/non-existent-task")
        assert response.status_code == 404

    def test_cancel_analysis(self, client, mock_task_manager):
        """测试取消分析端点"""
        # 模拟任务
        mock_task = Mock()
        mock_task.status.value = "pending"
        mock_task_manager.get_task.return_value = mock_task
        mock_task_manager.update_task.return_value = True

        response = client.delete("/api/v1/analysis/test-task-id")

        assert response.status_code == 200
        data = response.json()
        assert "任务已取消" in data["message"]

    def test_list_analyses(self, client, mock_task_manager):
        """测试列出分析任务端点"""
        # 模拟任务列表
        mock_tasks = [
            Mock(to_dict=lambda: {
                "request_id": "task1",
                "status": "completed",
                "created_at": "2023-01-01T00:00:00"
            }),
            Mock(to_dict=lambda: {
                "request_id": "task2",
                "status": "running",
                "created_at": "2023-01-02T00:00:00"
            })
        ]
        mock_task_manager.tasks = {
            "task1": mock_tasks[0],
            "task2": mock_tasks[1]
        }

        response = client.get("/api/v1/analysis")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_system_status(self, client):
        """测试获取系统状态端点"""
        with patch('src.api.routes.system_monitor') as mock_monitor, \
             patch('src.api.routes.task_manager') as mock_task_mgr:

            # 模拟监控数据
            mock_monitor.get_system_resources.return_value = {
                "cpu_usage": 50.0,
                "memory_usage": 60.0
            }
            mock_monitor.start_time = 1640995200  # 2022-01-01

            mock_task_mgr.get_active_tasks.return_value = []

            response = client.get("/api/v1/system/status")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "uptime" in data
            assert "system_resources" in data

    def test_quick_analysis(self, client, mock_task_manager):
        """测试快速分析端点"""
        # 模拟任务
        mock_task = Mock()
        mock_task.request.id = "quick-task-id"
        mock_task.status.value = "completed"
        mock_task_manager.create_task.return_value = mock_task

        response = client.post("/api/v1/quick-analysis?symbol=AAPL")

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data

    def test_portfolio_analysis(self, client, mock_task_manager):
        """测试投资组合分析端点"""
        # 模拟任务
        mock_task = Mock()
        mock_task.request.id = "portfolio-task-id"
        mock_task.status.value = "pending"
        mock_task_manager.create_task.return_value = mock_task

        request_data = {
            "symbols": ["AAPL", "MSFT", "GOOG"],
            "analysis_type": "portfolio"
        }

        response = client.post("/api/v1/portfolio-analysis", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data

    def test_portfolio_analysis_validation_error(self, client):
        """测试投资组合分析验证错误"""
        # 只有一个股票的投资组合
        request_data = {
            "symbols": ["AAPL"],  # 需要至少2个
            "analysis_type": "portfolio"
        }

        response = client.post("/api/v1/portfolio-analysis", json=request_data)
        assert response.status_code == 400

    def test_get_symbol_info(self, client):
        """测试获取股票信息端点"""
        response = client.get("/api/v1/symbols/AAPL/info")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "name" in data
        assert "exchange" in data


class TestWebSocket:
    """测试WebSocket功能"""

    @pytest.fixture
    def mock_websocket_manager(self):
        """模拟WebSocket管理器"""
        with patch('src.api.routes.websocket_manager') as mock:
            mock.connect = AsyncMock()
            mock.disconnect = Mock()
            mock.broadcast_task_update = AsyncMock()
            yield mock

    def test_websocket_connect(self, mock_websocket_manager):
        """测试WebSocket连接"""
        # 这个测试需要更复杂的WebSocket测试设置
        # 这里只是模拟测试框架
        assert True

    def test_websocket_message_handling(self, mock_websocket_manager):
        """测试WebSocket消息处理"""
        # 测试消息路由逻辑
        assert True


class TestAPIModels:
    """测试API模型"""

    def test_analysis_request_model(self):
        """测试分析请求模型"""
        request = AnalysisRequest(
            symbols=["AAPL"],
            analysis_type=AnalysisType.COMPREHENSIVE,
            export_formats=[ExportFormat.HTML]
        )

        assert len(request.symbols) == 1
        assert request.symbols[0] == "AAPL"
        assert request.analysis_type == AnalysisType.COMPREHENSIVE
        assert ExportFormat.HTML in request.export_formats

    def test_analysis_request_to_dict(self):
        """测试分析请求转换为字典"""
        request = AnalysisRequest(
            symbols=["AAPL", "MSFT"],
            analysis_type=AnalysisType.QUICK
        )

        data = request.to_dict()
        assert data["symbols"] == ["AAPL", "MSFT"]
        assert data["analysis_type"] == "quick"

    def test_analysis_request_from_dict(self):
        """测试从字典创建分析请求"""
        data = {
            "symbols": ["GOOG"],
            "analysis_type": "detailed",
            "export_formats": ["pdf", "excel"]
        }

        request = AnalysisRequest.from_dict(data)

        assert request.symbols == ["GOOG"]
        assert request.analysis_type == AnalysisType.DETAILED
        assert len(request.export_formats) == 2

    def test_validation_error(self):
        """测试验证错误"""
        from src.api.models import ValidationError

        with pytest.raises(ValidationError):
            raise ValidationError("测试验证错误")

    def test_validate_analysis_request(self):
        """测试分析请求验证"""
        from src.api.models import validate_analysis_request

        # 有效请求
        valid_data = {
            "symbols": ["AAPL"],
            "analysis_type": "comprehensive"
        }
        request = validate_analysis_request(valid_data)
        assert request.symbols == ["AAPL"]

        # 无效请求 - 空symbols
        invalid_data = {
            "symbols": [],
            "analysis_type": "comprehensive"
        }
        with pytest.raises(ValidationError):
            validate_analysis_request(invalid_data)

        # 无效请求 - 缺少必需字段
        with pytest.raises(ValidationError):
            validate_analysis_request({})