"""
FastAPI Application for AutoGen Financial Analysis System
Main application setup and configuration
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import logging
import uvicorn
from typing import Dict, List, Optional, Any
import redis
from datetime import datetime

from .models import (
    AnalysisRequest, AnalysisResponse, AnalysisTask,
    SystemStatus, ErrorResponse, AnalysisType, AnalysisStatus,
    validate_analysis_request, ValidationError
)
from .routes import api_routes
from .auth_routes import auth_routes
from .websocket import WebSocketManager
from ..config.config_manager import ConfigurationManager
from ..monitoring.monitoring_system import SystemMonitor
from ..security.security_manager import SecurityManager
from ..cache.cache_manager import CacheManager


class AnalysisTaskManager:
    """分析任务管理器"""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.tasks: Dict[str, AnalysisTask] = {}
        self.logger = logging.getLogger(__name__)

    async def create_task(self, request: AnalysisRequest) -> AnalysisTask:
        """创建分析任务"""
        task = AnalysisTask(request=request)
        self.tasks[task.request.id] = task
        return task

    async def get_task(self, task_id: str) -> Optional[AnalysisTask]:
        """获取任务"""
        return self.tasks.get(task_id)

    async def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False

        for key, value in kwargs.items():
            setattr(task, key, value)

        return True

    async def get_active_tasks(self) -> List[AnalysisTask]:
        """获取活跃任务"""
        return [task for task in self.tasks.values() if task.status == AnalysisStatus.RUNNING]

    async def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        tasks_to_remove = []

        for task_id, task in self.tasks.items():
            if (task.status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED] and
                task.completed_at and task.completed_at.timestamp() < cutoff_time):
                tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]

        if tasks_to_remove:
            self.logger.info(f"清理了 {len(tasks_to_remove)} 个已完成的任务")


# 全局变量
task_manager = None
websocket_manager = None
system_monitor = None
security_manager = None
cache_manager = None
config_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global task_manager, websocket_manager, system_monitor, security_manager, cache_manager, config_manager

    # 启动时初始化
    config_manager = ConfigurationManager("config.yaml")
    cache_manager = CacheManager(config_manager.get('cache.redis_url', 'redis://localhost:6379'))
    security_manager = SecurityManager(config_manager.get('security.secret_key', 'default-secret'))
    system_monitor = SystemMonitor()
    websocket_manager = WebSocketManager()
    task_manager = AnalysisTaskManager(cache_manager.redis_client)

    # 启动监控
    system_monitor.start_monitoring()

    # 启动后台任务
    asyncio.create_task(cleanup_background_tasks())

    yield

    # 关闭时清理
    if system_monitor:
        system_monitor.stop_monitoring()

    if cache_manager:
        await cache_manager.close()

    if websocket_manager:
        await websocket_manager.close()


def create_app() -> FastAPI:
    """创建FastAPI应用"""
    app = FastAPI(
        title="AutoGen Financial Analysis API",
        description="企业级AutoGen金融分析系统API",
        version="1.0.0",
        lifespan=lifespan
    )

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该配置具体的域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 静态文件服务
    try:
        app.mount("/static", StaticFiles(directory="web"), name="static")
    except Exception as e:
        logging.warning(f"Failed to mount static files: {e}")

    # 根路径 - 返回web界面
    @app.get("/")
    async def root():
        """根路径 - 返回web界面"""
        try:
            return FileResponse("web/index.html")
        except Exception:
            return JSONResponse({
                "message": "AutoGen Financial Analysis API",
                "version": "1.0.0",
                "docs": "/docs",
                "web_interface": "/static"
            })

    # 错误处理
    @app.exception_handler(ValidationError)
    async def validation_error_handler(request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error_code="VALIDATION_ERROR",
                error_message=str(exc)
            ).to_dict()
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request, exc: Exception):
        logging.error(f"未处理的异常: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INTERNAL_ERROR",
                error_message="内部服务器错误"
            ).to_dict()
        )

    # 包含路由
    app.include_router(api_routes, prefix="/api/v1")
    app.include_router(auth_routes, prefix="/api/v1")

    # WebSocket端点
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates"""
        from .routes import websocket_manager
        await websocket_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                # 处理WebSocket消息
                await websocket_manager.handle_message(websocket, data)
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)

    # 健康检查
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }

    return app


async def cleanup_background_tasks():
    """后台清理任务"""
    while True:
        try:
            await asyncio.sleep(3600)  # 每小时清理一次
            if task_manager:
                await task_manager.cleanup_completed_tasks()
        except Exception as e:
            logging.error(f"后台清理任务失败: {str(e)}")


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    # 开发服务器配置
    uvicorn.run(
        "src.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )