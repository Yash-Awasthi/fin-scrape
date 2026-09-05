"""线程安全的后台任务管理器"""
import asyncio
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("task_manager")

TASK_PENDING = "pending"
TASK_RUNNING = "running"
TASK_DONE = "done"
TASK_ERROR = "error"

STEP_IDLE = "idle"
STEP_RUNNING = "running"
STEP_DONE = "done"
STEP_ERROR = "error"

_event_loop: Optional[asyncio.AbstractEventLoop] = None


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _event_loop
    _event_loop = loop


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_to_ts(iso: Optional[str]) -> Optional[float]:
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


class TaskProgress:
    STEP_KEYS   = ["fetch", "cluster", "abstract", "theory", "scenario", "persist"]
    STEP_LABELS = ["新闻采集", "聚类分析", "事件抽象", "理论分析", "推演生成", "结果保存"]

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = TASK_PENDING
        self.created_at = _now_iso()
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.updated_at: str = self.created_at
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self._progress_detail: Optional[str] = None
        self._sub_progress: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()

        label_map = dict(zip(self.STEP_KEYS, self.STEP_LABELS))
        self.steps: List[Dict[str, Any]] = [
            {
                "key": key,
                "label": label_map.get(key, key),
                "status": STEP_IDLE,
                "started_at": None,
                "finished_at": None,
                "duration_seconds": None,
            }
            for key in self.STEP_KEYS
        ]

    def _touch(self):
        self.updated_at = _now_iso()

    def _broadcast_update(self):
        try:
            from backend.main import ws_manager
            loop = _event_loop
            if loop is None:
                loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    ws_manager.broadcast({
                        "type": "pipeline_progress",
                        "task_id": self.task_id,
                        "status": self.status,
                        "steps": self.steps,
                        "progress_detail": self._progress_detail,
                        "sub_progress": self._sub_progress,
                    }),
                    loop,
                )
        except Exception:
            pass

    def set_step(self, key: str, status: str):
        with self._lock:
            for step in self.steps:
                if step["key"] != key:
                    continue

                previous = step["status"]
                step["status"] = status
                now_iso = _now_iso()

                if status == STEP_RUNNING and previous != STEP_RUNNING:
                    step["started_at"] = now_iso
                    step["finished_at"] = None
                    step["duration_seconds"] = None
                elif status in (STEP_DONE, STEP_ERROR):
                    step["finished_at"] = now_iso
                    start_ts = _iso_to_ts(step.get("started_at"))
                    if start_ts is not None:
                        step["duration_seconds"] = round(time.time() - start_ts, 1)

                self._touch()
                break
        self._broadcast_update()

    def start(self):
        with self._lock:
            self.status = TASK_RUNNING
            self.started_at = _now_iso()
            self._touch()
        self._broadcast_update()

    def finish(self, result: Dict[str, Any]):
        with self._lock:
            self.status = TASK_DONE
            self.result = result
            self.finished_at = _now_iso()
            self._touch()
        self._broadcast_update()

    def fail(self, error: str):
        with self._lock:
            self.status = TASK_ERROR
            self.error = error
            self.finished_at = _now_iso()
            self._touch()

            now_iso = _now_iso()
            for step in self.steps:
                if step["status"] != STEP_RUNNING:
                    continue
                step["status"] = STEP_ERROR
                step["finished_at"] = now_iso
                start_ts = _iso_to_ts(step.get("started_at"))
                if start_ts is not None:
                    step["duration_seconds"] = round(time.time() - start_ts, 1)
        self._broadcast_update()

    def is_terminal(self) -> bool:
        return self.status in (TASK_DONE, TASK_ERROR)

    def set_progress_detail(self, detail: Optional[str]):
        with self._lock:
            self._progress_detail = detail
            self._touch()

    def get_progress_detail(self) -> Optional[str]:
        with self._lock:
            return self._progress_detail

    def set_sub_progress(self, current: int, total: int, label: str = ""):
        with self._lock:
            self._sub_progress = {"current": current, "total": total, "label": label}
            self._touch()

    def clear_sub_progress(self):
        with self._lock:
            self._sub_progress = None
            self._touch()

    def running_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        start_ts = _iso_to_ts(self.started_at)
        if start_ts is None:
            return 0.0
        end_ts = _iso_to_ts(self.finished_at) if self.finished_at else time.time()
        if end_ts is None:
            end_ts = time.time()
        return round(end_ts - start_ts, 1)

    def to_dict(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "task_id": self.task_id,
                "status": self.status,
                "created_at": self.created_at,
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "updated_at": self.updated_at,
                "running_seconds": self.running_seconds(),
                "error": self.error,
                "progress_detail": self._progress_detail,
                "sub_progress": self._sub_progress,
                "steps": [dict(step) for step in self.steps],
                "result": self.result,
            }


class TaskManager:
    # LLM重的任务可能很久，watchdog标记超时任务
    TASK_TIMEOUT_SECONDS = 5400

    def __init__(self, max_tasks: int = 50):
        self._tasks: Dict[str, TaskProgress] = {}
        self._lock = threading.Lock()
        self._max = max_tasks
        self._start_watchdog()

    def _start_watchdog(self):
        def _watch():
            while True:
                time.sleep(30)
                try:
                    self._check_timeouts()
                except Exception as exc:
                    logger.warning("[watchdog] timeout check error: %s", exc)

        t = threading.Thread(target=_watch, daemon=True, name="task-watchdog")
        t.start()
        logger.info("[task_manager] watchdog started (timeout=%ds)", self.TASK_TIMEOUT_SECONDS)

    def _check_timeouts(self):
        with self._lock:
            tasks = list(self._tasks.values())
        for task in tasks:
            if task.status != TASK_RUNNING or task.is_terminal():
                continue
            elapsed = task.running_seconds()
            if elapsed <= self.TASK_TIMEOUT_SECONDS:
                continue
            logger.error(
                "[watchdog] task %s timed out (%.0fs > %ds)",
                task.task_id,
                elapsed,
                self.TASK_TIMEOUT_SECONDS,
            )
            task.fail(f"Task timed out after {elapsed:.0f}s (limit: {self.TASK_TIMEOUT_SECONDS}s)")

    def create_task(self) -> TaskProgress:
        task_id = str(uuid.uuid4())
        task = TaskProgress(task_id)
        with self._lock:
            if len(self._tasks) >= self._max:
                oldest = sorted(self._tasks.values(), key=lambda item: item.created_at)
                for old in oldest[: len(self._tasks) - self._max + 1]:
                    del self._tasks[old.task_id]
            self._tasks[task_id] = task
        return task

    def get(self, task_id: str) -> Optional[TaskProgress]:
        with self._lock:
            return self._tasks.get(task_id)

    def run_in_thread(self, task: TaskProgress, fn: Callable, *args, **kwargs):
        def wrapper():
            task.start()
            try:
                result = fn(task, *args, **kwargs)
                task.finish(result)
            except Exception as exc:
                logger.exception("[task_manager] task %s failed: %s", task.task_id, exc)
                task.fail(str(exc))

        t = threading.Thread(target=wrapper, daemon=True, name=f"task-{task.task_id[:8]}")
        t.start()


task_manager = TaskManager()
