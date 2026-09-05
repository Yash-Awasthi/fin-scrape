"""
Concurrency Manager
Advanced concurrency management with thread pools, process pools, and resource balancing
"""

import asyncio
import threading
import multiprocessing
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Callable, Any, TypeVar, Union
from dataclasses import dataclass, field
from enum import Enum
import queue
import logging
import psutil
import weakref
import os

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConcurrencyStrategy(Enum):
    """Concurrency execution strategies"""
    THREAD_POOL = "thread_pool"
    PROCESS_POOL = "process_pool"
    ASYNC = "async"
    MIXED = "mixed"
    ADAPTIVE = "adaptive"


@dataclass
class ThreadPoolConfig:
    """Thread pool configuration"""
    max_workers: Optional[int] = None
    thread_name_prefix: str = "worker"
    worker_init_fn: Optional[Callable] = None
    worker_init_args: tuple = field(default_factory=tuple)


@dataclass
class ProcessPoolConfig:
    """Process pool configuration"""
    max_workers: Optional[int] = None
    mp_context: Optional[Any] = None
    initializer: Optional[Callable] = None
    initargs: tuple = field(default_factory=tuple)
    max_tasks_per_child: Optional[int] = None


class ConcurrencyManager:
    """Advanced concurrency management with resource awareness"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Resource limits
        self.max_cpu_percent = self.config.get('max_cpu_percent', 80)
        self.max_memory_percent = self.config.get('max_memory_percent', 80)
        self.max_workers = self.config.get('max_workers', multiprocessing.cpu_count())

        # Strategy
        self.strategy = ConcurrencyStrategy(self.config.get('strategy', 'adaptive'))

        # Initialize pools
        self.thread_pool_config = ThreadPoolConfig(
            max_workers=self.config.get('thread_pool_workers', self.max_workers),
            thread_name_prefix=self.config.get('thread_name_prefix', 'concurrent_worker')
        )

        self.process_pool_config = ProcessPoolConfig(
            max_workers=self.config.get('process_pool_workers', self.max_workers),
            max_tasks_per_child=self.config.get('max_tasks_per_child', 100)
        )

        # Pool instances
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.process_pool: Optional[ProcessPoolExecutor] = None

        # Resource monitoring
        self.resource_monitor_thread = None
        self.monitoring = False
        self.stop_event = threading.Event()

        # Adaptive management
        self.adaptive_enabled = self.strategy == ConcurrencyStrategy.ADAPTIVE
        self.resource_history: List[Dict[str, float]] = []
        self.max_history_size = 100

        # Statistics
        self.stats = {
            'thread_tasks': 0,
            'process_tasks': 0,
            'async_tasks': 0,
            'total_tasks': 0,
            'failed_tasks': 0,
            'avg_cpu_usage': 0.0,
            'avg_memory_usage': 0.0
        }

        # Initialize based on strategy
        self._initialize_strategy()

        logger.info(f"Concurrency Manager initialized with strategy: {self.strategy.value}")

    def _initialize_strategy(self):
        """Initialize execution strategy"""
        if self.strategy == ConcurrencyStrategy.THREAD_POOL:
            self._initialize_thread_pool()
        elif self.strategy == ConcurrencyStrategy.PROCESS_POOL:
            self._initialize_process_pool()
        elif self.strategy == ConcurrencyStrategy.MIXED:
            self._initialize_thread_pool()
            self._initialize_process_pool()
        elif self.strategy in [ConcurrencyStrategy.ASYNC, ConcurrencyStrategy.ADAPTIVE]:
            self._initialize_thread_pool()
            self.start_resource_monitoring()

    def _initialize_thread_pool(self):
        """Initialize thread pool"""
        if self.thread_pool is None:
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.thread_pool_config.max_workers,
                thread_name_prefix=self.thread_pool_config.thread_name_prefix,
                initializer=self.thread_pool_config.worker_init_fn,
                initargs=self.thread_pool_config.worker_init_args
            )
            logger.info(f"Thread pool initialized with {self.thread_pool._max_workers} workers")

    def _initialize_process_pool(self):
        """Initialize process pool"""
        if self.process_pool is None:
            self.process_pool = ProcessPoolExecutor(
                max_workers=self.process_pool_config.max_workers,
                mp_context=self.process_pool_config.mp_context,
                initializer=self.process_pool_config.initializer,
                initargs=self.process_pool_config.initargs,
                max_tasks_per_child=self.process_pool_config.max_tasks_per_child
            )
            logger.info(f"Process pool initialized with {self.process_pool._max_workers} workers")

    def start_resource_monitoring(self):
        """Start resource monitoring thread"""
        if self.monitoring:
            return

        self.monitoring = True
        self.stop_event.clear()
        self.resource_monitor_thread = threading.Thread(target=self._monitor_resources)
        self.resource_monitor_thread.daemon = True
        self.resource_monitor_thread.start()

        logger.info("Resource monitoring started")

    def stop_resource_monitoring(self):
        """Stop resource monitoring"""
        if not self.monitoring:
            return

        self.monitoring = False
        self.stop_event.set()
        if self.resource_monitor_thread:
            self.resource_monitor_thread.join(timeout=5)

        logger.info("Resource monitoring stopped")

    def _monitor_resources(self):
        """Resource monitoring loop"""
        while not self.stop_event.is_set():
            try:
                # Get current resource usage
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_percent = psutil.virtual_memory().percent

                # Update history
                self.resource_history.append({
                    'cpu': cpu_percent,
                    'memory': memory_percent,
                    'timestamp': time.time()
                })

                # Maintain history size
                if len(self.resource_history) > self.max_history_size:
                    self.resource_history = self.resource_history[-self.max_history_size:]

                # Update averages
                self.stats['avg_cpu_usage'] = sum(h['cpu'] for h in self.resource_history) / len(self.resource_history)
                self.stats['avg_memory_usage'] = sum(h['memory'] for h in self.resource_history) / len(self.resource_history)

                # Adaptive adjustment
                if self.adaptive_enabled:
                    self._adjust_resources(cpu_percent, memory_percent)

                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(1)

    def _adjust_resources(self, cpu_percent: float, memory_percent: float):
        """Adjust resources based on current usage"""
        # CPU-based adjustment
        if cpu_percent > self.max_cpu_percent:
            self._reduce_concurrency('cpu')
        elif cpu_percent < self.max_cpu_percent * 0.7:
            self._increase_concurrency('cpu')

        # Memory-based adjustment
        if memory_percent > self.max_memory_percent:
            self._reduce_concurrency('memory')
        elif memory_percent < self.max_memory_percent * 0.7:
            self._increase_concurrency('memory')

    def _reduce_concurrency(self, reason: str):
        """Reduce concurrency due to resource constraints"""
        if self.thread_pool and self.thread_pool._max_workers > 2:
            new_max = max(2, self.thread_pool._max_workers - 1)
            self.thread_pool._max_workers = new_max
            logger.info(f"Reduced thread pool workers to {new_max} due to {reason} constraints")

    def _increase_concurrency(self, reason: str):
        """Increase concurrency if resources allow"""
        if self.thread_pool and self.thread_pool._max_workers < self.max_workers:
            new_max = min(self.max_workers, self.thread_pool._max_workers + 1)
            self.thread_pool._max_workers = new_max
            logger.info(f"Increased thread pool workers to {new_max} due to {reason} availability")

    def execute_threaded(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function in thread pool"""
        if self.thread_pool is None:
            self._initialize_thread_pool()

        try:
            future = self.thread_pool.submit(func, *args, **kwargs)
            result = future.result()
            self.stats['thread_tasks'] += 1
            self.stats['total_tasks'] += 1
            return result
        except Exception as e:
            self.stats['failed_tasks'] += 1
            logger.error(f"Thread execution failed: {e}")
            raise

    def execute_multiprocess(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function in process pool"""
        if self.process_pool is None:
            self._initialize_process_pool()

        try:
            future = self.process_pool.submit(func, *args, **kwargs)
            result = future.result()
            self.stats['process_tasks'] += 1
            self.stats['total_tasks'] += 1
            return result
        except Exception as e:
            self.stats['failed_tasks'] += 1
            logger.error(f"Process execution failed: {e}")
            raise

    def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function"""
        if asyncio.iscoroutinefunction(func):
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(func(*args, **kwargs))
                self.stats['async_tasks'] += 1
                self.stats['total_tasks'] += 1
                return result
            except Exception as e:
                self.stats['failed_tasks'] += 1
                logger.error(f"Async execution failed: {e}")
                raise
        else:
            # Fallback to thread pool for sync functions
            return self.execute_threaded(func, *args, **kwargs)

    def execute_adaptive(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function using adaptive strategy"""
        # Determine best execution method based on current resources
        current_cpu = self.stats['avg_cpu_usage']
        current_memory = self.stats['avg_memory_usage']

        # Decision logic
        if current_cpu > 90 or current_memory > 90:
            # High resource usage - use thread pool (lighter)
            return self.execute_threaded(func, *args, **kwargs)
        elif current_cpu < 50 and current_memory < 50:
            # Low resource usage - can use process pool for CPU-bound tasks
            return self.execute_multiprocess(func, *args, **kwargs)
        else:
            # Medium usage - use thread pool for safety
            return self.execute_threaded(func, *args, **kwargs)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function using configured strategy"""
        if self.strategy == ConcurrencyStrategy.THREAD_POOL:
            return self.execute_threaded(func, *args, **kwargs)
        elif self.strategy == ConcurrencyStrategy.PROCESS_POOL:
            return self.execute_multiprocess(func, *args, **kwargs)
        elif self.strategy == ConcurrencyStrategy.ASYNC:
            return self.execute_async(func, *args, **kwargs)
        elif self.strategy == ConcurrencyStrategy.MIXED:
            # Simple mixed strategy - alternate between thread and process
            if self.stats['total_tasks'] % 2 == 0:
                return self.execute_threaded(func, *args, **kwargs)
            else:
                return self.execute_multiprocess(func, *args, **kwargs)
        elif self.strategy == ConcurrencyStrategy.ADAPTIVE:
            return self.execute_adaptive(func, *args, **kwargs)

    def map_threaded(self, func: Callable, iterable: List[Any]) -> List[Any]:
        """Map function over iterable using thread pool"""
        if self.thread_pool is None:
            self._initialize_thread_pool()

        try:
            results = list(self.thread_pool.map(func, iterable))
            self.stats['thread_tasks'] += len(iterable)
            self.stats['total_tasks'] += len(iterable)
            return results
        except Exception as e:
            self.stats['failed_tasks'] += len(iterable)
            logger.error(f"Threaded map failed: {e}")
            raise

    def map_multiprocess(self, func: Callable, iterable: List[Any]) -> List[Any]:
        """Map function over iterable using process pool"""
        if self.process_pool is None:
            self._initialize_process_pool()

        try:
            results = list(self.process_pool.map(func, iterable))
            self.stats['process_tasks'] += len(iterable)
            self.stats['total_tasks'] += len(iterable)
            return results
        except Exception as e:
            self.stats['failed_tasks'] += len(iterable)
            logger.error(f"Multiprocess map failed: {e}")
            raise

    def submit_concurrent(self, tasks: List[Dict[str, Any]]) -> List[Any]:
        """Submit multiple tasks for concurrent execution"""
        if not tasks:
            return []

        futures = []
        for task in tasks:
            func = task['func']
            args = task.get('args', ())
            kwargs = task.get('kwargs', {})

            future = self.thread_pool.submit(func, *args, **kwargs) if self.thread_pool else None
            if future:
                futures.append(future)

        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                self.stats['total_tasks'] += 1
            except Exception as e:
                self.stats['failed_tasks'] += 1
                results.append(None)
                logger.error(f"Concurrent task failed: {e}")

        return results

    def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'memory_percent': psutil.virtual_memory().percent,
            'thread_workers': self.thread_pool._max_workers if self.thread_pool else 0,
            'process_workers': self.process_pool._max_workers if self.process_pool else 0,
            'active_threads': len(threading.enumerate()),
            'active_processes': len(psutil.pids())
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get concurrency statistics"""
        return {
            **self.stats,
            'strategy': self.strategy.value,
            'resource_usage': self.get_resource_usage(),
            'queue_sizes': {
                'thread_pool': self.thread_pool._work_queue.qsize() if self.thread_pool else 0,
                'process_pool': self.process_pool._call_queue.qsize() if self.process_pool else 0
            }
        }

    def shutdown(self, wait: bool = True):
        """Shutdown all executor pools"""
        logger.info("Shutting down concurrency manager")

        self.stop_resource_monitoring()

        if self.thread_pool:
            self.thread_pool.shutdown(wait=wait)
            self.thread_pool = None

        if self.process_pool:
            self.process_pool.shutdown(wait=wait)
            self.process_pool = None

        logger.info("Concurrency manager shutdown complete")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


# Global instances
_concurrency_manager: Optional[ConcurrencyManager] = None


def get_concurrency_manager(config: Dict[str, Any] = None) -> ConcurrencyManager:
    """Get or create the global concurrency manager instance"""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ConcurrencyManager(config)
    return _concurrency_manager


def run_threaded(func: Callable, *args, **kwargs) -> Any:
    """Run function in thread pool"""
    manager = get_concurrency_manager()
    return manager.execute_threaded(func, *args, **kwargs)


def run_multiprocess(func: Callable, *args, **kwargs) -> Any:
    """Run function in process pool"""
    manager = get_concurrency_manager()
    return manager.execute_multiprocess(func, *args, **kwargs)


def manage_concurrency(func: Callable, *args, **kwargs) -> Any:
    """Run function using configured concurrency strategy"""
    manager = get_concurrency_manager()
    return manager.execute(func, *args, **kwargs)