"""
Async Processor
Advanced asynchronous task processing with priority, batching, and result caching
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import weakref
import pickle

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AsyncTask:
    """Asynchronous task definition"""
    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    callback: Optional[Callable] = None
    depends_on: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BatchProcessor:
    """Batch processor for efficient handling of multiple tasks"""

    def __init__(self, batch_size: int = 10, max_wait_time: float = 1.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_tasks: List[AsyncTask] = []
        self.last_batch_time = datetime.now()

    def add_task(self, task: AsyncTask) -> bool:
        """Add task to batch"""
        self.pending_tasks.append(task)
        return self._should_process_batch()

    def _should_process_batch(self) -> bool:
        """Check if batch should be processed"""
        return (
            len(self.pending_tasks) >= self.batch_size or
            (datetime.now() - self.last_batch_time).total_seconds() >= self.max_wait_time
        )

    def get_batch(self) -> List[AsyncTask]:
        """Get current batch for processing"""
        if not self._should_process_batch():
            return []

        batch = self.pending_tasks[:self.batch_size]
        self.pending_tasks = self.pending_tasks[self.batch_size:]
        self.last_batch_time = datetime.now()
        return batch

    def get_pending_count(self) -> int:
        """Get number of pending tasks"""
        return len(self.pending_tasks)


class AsyncProcessor:
    """Advanced asynchronous task processor"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Thread pool settings
        self.max_workers = self.config.get('max_workers', 10)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)

        # Task storage
        self.tasks: Dict[str, AsyncTask] = {}
        self.results: Dict[str, TaskResult] = {}
        self.task_queue = queue.PriorityQueue()

        # Dependencies
        self.task_dependencies: Dict[str, List[str]] = {}

        # Batch processing
        self.batch_processor = BatchProcessor(
            batch_size=self.config.get('batch_size', 10),
            max_wait_time=self.config.get('max_wait_time', 1.0)
        )

        # Processing control
        self._processing = False
        self._process_thread = None
        self._stop_event = threading.Event()

        # Caching
        self.enable_caching = self.config.get('enable_caching', True)
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1 hour
        self.task_cache: Dict[str, Any] = {}

        # Event loop for async operations
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Statistics
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_duration': 0.0,
            'cache_hits': 0
        }

        logger.info(f"Async Processor initialized with {self.max_workers} workers")

    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit a task for asynchronous execution"""
        task_id = str(uuid.uuid4())

        # Extract task-specific parameters
        priority = kwargs.pop('priority', TaskPriority.NORMAL)
        timeout = kwargs.pop('timeout', None)
        max_retries = kwargs.pop('max_retries', 3)
        callback = kwargs.pop('callback', None)
        depends_on = kwargs.pop('depends_on', [])
        tags = kwargs.pop('tags', [])
        metadata = kwargs.pop('metadata', {})

        # Create task
        task = AsyncTask(
            task_id=task_id,
            name=func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            max_retries=max_retries,
            callback=callback,
            depends_on=depends_on,
            tags=tags,
            metadata=metadata
        )

        self.tasks[task_id] = task
        self.task_queue.put((priority.value, task_id))

        # Check cache
        if self.enable_caching and self._is_cacheable(task):
            cache_key = self._get_cache_key(task)
            if cache_key in self.task_cache:
                cached_result = self.task_cache[cache_key]
                if self._is_cache_valid(cached_result):
                    self._complete_task(task_id, cached_result['result'])
                    self.stats['cache_hits'] += 1
                    return task_id

        self.stats['tasks_submitted'] += 1
        logger.debug(f"Task submitted: {task_id} - {task.name}")

        return task_id

    def submit_batch(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Submit multiple tasks as a batch"""
        task_ids = []
        for task_def in tasks:
            task_id = self.submit_task(**task_def)
            task_ids.append(task_id)
        return task_ids

    def start_processing(self):
        """Start the task processing loop"""
        if self._processing:
            return

        self._processing = True
        self._stop_event.clear()
        self._process_thread = threading.Thread(target=self._process_loop)
        self._process_thread.daemon = True
        self._process_thread.start()

        logger.info("Async processing started")

    def stop_processing(self):
        """Stop the task processing loop"""
        if not self._processing:
            return

        self._processing = False
        self._stop_event.set()
        if self._process_thread:
            self._process_thread.join(timeout=10)

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)

        logger.info("Async processing stopped")

    def _process_loop(self):
        """Main processing loop"""
        while self._processing:
            try:
                # Check for batch processing
                batch = self.batch_processor.get_batch()
                if batch:
                    self._process_batch(batch)
                    continue

                # Process single task
                try:
                    priority, task_id = self.task_queue.get(timeout=0.1)
                    task = self.tasks.get(task_id)

                    if task and self._can_execute_task(task):
                        self._execute_task(task)
                    elif task:
                        # Re-queue if dependencies not met
                        self.task_queue.put((priority, task_id))

                except queue.Empty:
                    continue

            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(0.1)

    def _process_batch(self, batch: List[AsyncTask]):
        """Process a batch of tasks"""
        logger.debug(f"Processing batch of {len(batch)} tasks")

        futures = []
        for task in batch:
            if self._can_execute_task(task):
                future = self.thread_pool.submit(self._execute_task_sync, task)
                futures.append((task.task_id, future))

        # Wait for completion
        for task_id, future in futures:
            try:
                future.result(timeout=task.timeout)
            except Exception as e:
                logger.error(f"Error in batch task {task_id}: {e}")

    def _can_execute_task(self, task: AsyncTask) -> bool:
        """Check if task can be executed (dependencies met)"""
        if not task.depends_on:
            return True

        for dep_id in task.depends_on:
            if dep_id not in self.results:
                return False
            if self.results[dep_id].status != TaskStatus.COMPLETED:
                return False

        return True

    def _execute_task(self, task: AsyncTask):
        """Execute a task asynchronously"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            # Execute in thread pool
            future = self.thread_pool.submit(self._execute_task_sync, task)
            result = future.result(timeout=task.timeout)

            self._complete_task(task.task_id, result)

        except Exception as e:
            self._handle_task_error(task, e)

    def _execute_task_sync(self, task: AsyncTask) -> Any:
        """Execute task synchronously"""
        logger.debug(f"Executing task: {task.task_id} - {task.name}")

        try:
            # Execute the function
            if asyncio.iscoroutinefunction(task.func):
                # For async functions, run in event loop
                result = self._loop.run_until_complete(task.func(*task.args, **task.kwargs))
            else:
                result = task.func(*task.args, **task.kwargs)

            return result

        except Exception as e:
            logger.error(f"Task execution failed: {task.task_id} - {e}")
            raise

    def _complete_task(self, task_id: str, result: Any):
        """Complete a task successfully"""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()
        task.result = result

        # Store result
        duration = (task.completed_at - task.started_at).total_seconds()
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            result=result,
            duration=duration,
            retry_count=task.retry_count,
            metadata=task.metadata
        )
        self.results[task_id] = task_result

        # Cache result
        if self.enable_caching and self._is_cacheable(task):
            self._cache_result(task, result)

        # Execute callback
        if task.callback:
            try:
                task.callback(result)
            except Exception as e:
                logger.error(f"Error in task callback: {e}")

        # Update statistics
        self.stats['tasks_completed'] += 1
        self.stats['total_duration'] += duration

        logger.debug(f"Task completed: {task_id} in {duration:.2f}s")

    def _handle_task_error(self, task: AsyncTask, error: Exception):
        """Handle task execution error"""
        task.error = error

        if task.retry_count < task.max_retries:
            # Retry the task
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            self.task_queue.put((task.priority.value, task.task_id))
            logger.info(f"Retrying task {task.task_id} (attempt {task.retry_count}/{task.max_retries})")
        else:
            # Mark as failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

            task_result = TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=error,
                retry_count=task.retry_count,
                metadata=task.metadata
            )
            self.results[task.task_id] = task_result

            self.stats['tasks_failed'] += 1
            logger.error(f"Task failed: {task.task_id} - {error}")

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        return task.status if task else None

    def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """Get result of a specific task"""
        if task_id in self.results:
            return self.results[task_id]

        if timeout:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if task_id in self.results:
                    return self.results[task_id]
                time.sleep(0.1)

        return None

    def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> bool:
        """Wait for a task to complete"""
        start_time = time.time()
        while timeout is None or time.time() - start_time < timeout:
            if task_id in self.results:
                return True
            time.sleep(0.1)
        return False

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()

            task_result = TaskResult(
                task_id=task_id,
                status=TaskStatus.CANCELLED,
                metadata=task.metadata
            )
            self.results[task_id] = task_result

            logger.info(f"Task cancelled: {task_id}")
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            **self.stats,
            'pending_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            'running_tasks': len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING]),
            'cache_size': len(self.task_cache),
            'queue_size': self.task_queue.qsize()
        }

    def clear_cache(self):
        """Clear the task cache"""
        self.task_cache.clear()
        logger.info("Task cache cleared")

    def _is_cacheable(self, task: AsyncTask) -> bool:
        """Check if task result should be cached"""
        return not task.metadata.get('no_cache', False)

    def _get_cache_key(self, task: AsyncTask) -> str:
        """Generate cache key for task"""
        # Create a hashable representation of the task
        key_data = {
            'name': task.name,
            'args': task.args,
            'kwargs': task.kwargs
        }
        return str(hash(pickle.dumps(key_data)))

    def _cache_result(self, task: AsyncTask, result: Any):
        """Cache task result"""
        cache_key = self._get_cache_key(task)
        self.task_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.now(),
            'task_id': task.task_id
        }

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """Check if cached result is still valid"""
        timestamp = cached_data['timestamp']
        return (datetime.now() - timestamp).total_seconds() < self.cache_ttl

    def cleanup_old_cache(self):
        """Clean up expired cache entries"""
        current_time = datetime.now()
        expired_keys = []

        for key, data in self.task_cache.items():
            if (current_time - data['timestamp']).total_seconds() > self.cache_ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.task_cache[key]

        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def __del__(self):
        """Cleanup on destruction"""
        self.stop_processing()
        if hasattr(self, '_loop'):
            self._loop.close()


# Global instances
_async_processor: Optional[AsyncProcessor] = None


def get_async_processor(config: Dict[str, Any] = None) -> AsyncProcessor:
    """Get or create the global async processor instance"""
    global _async_processor
    if _async_processor is None:
        _async_processor = AsyncProcessor(config)
        _async_processor.start_processing()
    return _async_processor


def process_async(func: Callable, *args, **kwargs) -> str:
    """Process a function asynchronously"""
    processor = get_async_processor()
    return processor.submit_task(func, *args, **kwargs)


def process_batch(tasks: List[Dict[str, Any]]) -> List[str]:
    """Process multiple tasks as a batch"""
    processor = get_async_processor()
    return processor.submit_batch(tasks)


def run_concurrent(funcs: List[Callable], args_list: List[tuple] = None) -> List[Any]:
    """Run multiple functions concurrently"""
    if args_list is None:
        args_list = [() for _ in funcs]

    processor = get_async_processor()
    task_ids = []

    for func, args in zip(funcs, args_list):
        task_id = processor.submit_task(func, *args)
        task_ids.append(task_id)

    # Wait for all tasks to complete
    results = []
    for task_id in task_ids:
        result = processor.get_task_result(task_id, timeout=300)  # 5 minute timeout
        results.append(result.result if result else None)

    return results