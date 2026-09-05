"""
tests/conftest.py
FastAPI TestClient fixture — 不依赖 Claude API，不发外网请求
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """
    创建 FastAPI TestClient。
    startup 事件会运行（初始化 SQLite），但外部依赖检测是异步 task，
    TestClient 不会等它完成，所以不会阻塞测试。
    """
    # 设置测试用环境变量（避免 .env 中的真实 key 影响测试）
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-fake-key-for-testing")
    os.environ.setdefault("DEBUG", "true")

    from backend.main import app
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
