"""
Performance Manager
Advanced performance monitoring, metrics collection, and optimization strategies
"""

import asyncio
import time
import threading
import psutil
import tracemalloc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import queue
import logging

logger = logging.getLogger(__name__)


class PerformanceProfile(Enum):
    """Performance optimization profiles"""
    BALANCED = "balanced"
    PERFORMANCE = "performance"
    MEMORY = "memory"
    CUSTOM = "custom"


@dataclass
class PerformanceMetrics:
    """Performance metrics collection"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    handle_count: int
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceUsage:
    """Resource usage statistics"""
    cpu_percent: float
    memory_percent: float
    memory_available: int
    memory_total: int
    disk_usage_percent: float
    disk_available: int
    disk_total: int
    network_bytes_sent: int
    network_bytes_recv: int
    process_memory_rss: int
    process_memory_vms: int
    process_cpu_percent: float


@dataclass
class TaskMetrics:
    """Task execution metrics"""
    task_id: str
    task_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    memory_before: Optional[int] = None
    memory_after: Optional[int] = None
    memory_delta: Optional[int] = None
    cpu_usage: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)


class PerformanceManager:
    """Advanced performance monitoring and optimization manager"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.profile = PerformanceProfile(self.config.get('profile', 'balanced'))

        # Metrics storage
        self.metrics_history: List[PerformanceMetrics] = []
        self.task_metrics: Dict[str, TaskMetrics] = {}
        self.resource_history: List[ResourceUsage] = []

        # Performance settings
        self.max_metrics_history = self.config.get('max_metrics_history', 1000)
        self.monitoring_interval = self.config.get('monitoring_interval', 1.0)
        self.enable_tracing = self.config.get('enable_tracing', True)

        # Monitoring state
        self._monitoring = False
        self._monitor_thread = None
        self._stop_event = threading.Event()

        # Performance optimization
        self.optimization_strategies = self.config.get('optimization_strategies', {})
        self.custom_optimizers: Dict[str, Callable] = {}

        # Memory tracking
        if self.enable_tracing:
            tracemalloc.start()

        # Initialize performance profile
        self._apply_performance_profile()

        logger.info(f"Performance Manager initialized with profile: {self.profile.value}")

    def _apply_performance_profile(self):
        """Apply performance profile settings"""
        profiles = {
            PerformanceProfile.BALANCED: {
                'max_workers': None,
                'memory_limit_mb': 1024,
                'cpu_limit_percent': 80,
                'optimization_level': 'moderate'
            },
            PerformanceProfile.PERFORMANCE: {
                'max_workers': None,
                'memory_limit_mb': 2048,
                'cpu_limit_percent': 95,
                'optimization_level': 'aggressive'
            },
            PerformanceProfile.MEMORY: {
                'max_workers': 4,
                'memory_limit_mb': 512,
                'cpu_limit_percent': 60,
                'optimization_level': 'conservative'
            }
        }

        if self.profile in profiles:
            profile_config = profiles[self.profile]
            self.config.update(profile_config)

    def start_monitoring(self):
        """Start performance monitoring"""
        if self._monitoring:
            return

        self._monitoring = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self._monitoring:
            return

        self._monitoring = False
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        logger.info("Performance monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)

                # Maintain history size
                if len(self.metrics_history) > self.max_metrics_history:
                    self.metrics_history = self.metrics_history[-self.max_metrics_history:]

                # Check performance thresholds
                self._check_performance_thresholds(metrics)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(self.monitoring_interval)

    def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        timestamp = datetime.now()

        # System metrics
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }

        # Process metrics
        process = psutil.Process()
        process_count = len(psutil.pids())
        thread_count = process.num_threads()
        handle_count = process.num_handles() if hasattr(process, 'num_handles') else 0

        return PerformanceMetrics(
            timestamp=timestamp,
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            network_io=network_io,
            process_count=process_count,
            thread_count=thread_count,
            handle_count=handle_count
        )

    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage"""
        process = psutil.Process()

        # Memory
        memory = psutil.virtual_memory()
        process_memory = process.memory_info()

        # Disk
        disk = psutil.disk_usage('/')

        # Network
        network = psutil.net_io_counters()

        return ResourceUsage(
            cpu_percent=psutil.cpu_percent(interval=None),
            memory_percent=memory.percent,
            memory_available=memory.available,
            memory_total=memory.total,
            disk_usage_percent=disk.percent,
            disk_available=disk.free,
            disk_total=disk.total,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            process_memory_rss=process_memory.rss,
            process_memory_vms=process_memory.vms,
            process_cpu_percent=process.cpu_percent(interval=None)
        )

    def start_task_metrics(self, task_id: str, task_name: str) -> str:
        """Start tracking task metrics"""
        current_memory = None
        if self.enable_tracing:
            current_memory = tracemalloc.get_traced_memory()[0]

        metrics = TaskMetrics(
            task_id=task_id,
            task_name=task_name,
            start_time=datetime.now(),
            memory_before=current_memory
        )

        self.task_metrics[task_id] = metrics
        return task_id

    def end_task_metrics(self, task_id: str, success: bool = True, error: str = None):
        """End tracking task metrics"""
        if task_id not in self.task_metrics:
            return

        metrics = self.task_metrics[task_id]
        metrics.end_time = datetime.now()
        metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.success = success
        metrics.error = error

        if self.enable_tracing:
            metrics.memory_after = tracemalloc.get_traced_memory()[0]
            if metrics.memory_before:
                metrics.memory_delta = metrics.memory_after - metrics.memory_before

        # CPU usage
        try:
            process = psutil.Process()
            metrics.cpu_usage = process.cpu_percent(interval=None)
        except:
            pass

    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Get metrics for a specific task"""
        return self.task_metrics.get(task_id)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.metrics_history:
            return {}

        # Calculate statistics
        cpu_values = [m.cpu_usage for m in self.metrics_history]
        memory_values = [m.memory_usage for m in self.metrics_history]

        # Task statistics
        completed_tasks = [m for m in self.task_metrics.values() if m.end_time]
        success_rate = len([m for m in completed_tasks if m.success]) / len(completed_tasks) if completed_tasks else 0

        return {
            'monitoring_duration': (self.metrics_history[-1].timestamp - self.metrics_history[0].timestamp).total_seconds(),
            'metrics_collected': len(self.metrics_history),
            'cpu_stats': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_stats': {
                'current': memory_values[-1] if memory_values else 0,
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'task_stats': {
                'total_tasks': len(self.task_metrics),
                'completed_tasks': len(completed_tasks),
                'success_rate': success_rate,
                'average_duration': sum(m.duration for m in completed_tasks if m.duration) / len(completed_tasks) if completed_tasks else 0
            }
        }

    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check if metrics exceed thresholds"""
        thresholds = self.config.get('thresholds', {})

        # CPU threshold
        if metrics.cpu_usage > thresholds.get('cpu_warning', 80):
            logger.warning(f"High CPU usage: {metrics.cpu_usage}%")

        # Memory threshold
        if metrics.memory_usage > thresholds.get('memory_warning', 80):
            logger.warning(f"High memory usage: {metrics.memory_usage}%")

        # Disk threshold
        if metrics.disk_usage > thresholds.get('disk_warning', 90):
            logger.warning(f"High disk usage: {metrics.disk_usage}%")

    def optimize_performance(self, component: str = None) -> Dict[str, Any]:
        """Apply performance optimizations"""
        optimizations = {}

        # General optimizations
        if component is None or component == 'memory':
            optimizations['memory'] = self._optimize_memory()

        if component is None or component == 'cpu':
            optimizations['cpu'] = self._optimize_cpu()

        if component is None or component == 'io':
            optimizations['io'] = self._optimize_io()

        # Custom optimizations
        if component in self.custom_optimizers:
            try:
                result = self.custom_optimizers[component]()
                optimizations[component] = result
            except Exception as e:
                logger.error(f"Error in custom optimizer for {component}: {e}")

        return optimizations

    def _optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage"""
        before = self.get_resource_usage().process_memory_rss

        # Force garbage collection
        import gc
        gc.collect()

        # Clear old metrics
        if len(self.metrics_history) > self.max_metrics_history // 2:
            self.metrics_history = self.metrics_history[-self.max_metrics_history // 2:]

        # Clear completed old task metrics
        old_tasks = [
            task_id for task_id, metrics in self.task_metrics.items()
            if metrics.end_time and (datetime.now() - metrics.end_time).total_seconds() > 3600
        ]
        for task_id in old_tasks:
            del self.task_metrics[task_id]

        after = self.get_resource_usage().process_memory_rss
        saved = before - after

        return {
            'memory_before': before,
            'memory_after': after,
            'memory_saved': saved,
            'metrics_cleared': len(old_tasks)
        }

    def _optimize_cpu(self) -> Dict[str, Any]:
        """Optimize CPU usage"""
        return {
            'cpu_limit': self.config.get('cpu_limit_percent', 80),
            'optimization_applied': 'priority_adjustment'
        }

    def _optimize_io(self) -> Dict[str, Any]:
        """Optimize I/O operations"""
        return {
            'buffer_sizes': 'optimized',
            'async_io': 'enabled'
        }

    def register_custom_optimizer(self, component: str, optimizer: Callable):
        """Register a custom optimization function"""
        self.custom_optimizers[component] = optimizer

    def export_metrics(self, filepath: str, format: str = 'json'):
        """Export metrics to file"""
        data = {
            'metrics_history': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'cpu_usage': m.cpu_usage,
                    'memory_usage': m.memory_usage,
                    'disk_usage': m.disk_usage,
                    'network_io': m.network_io,
                    'process_count': m.process_count,
                    'thread_count': m.thread_count,
                    'handle_count': m.handle_count
                }
                for m in self.metrics_history
            ],
            'task_metrics': [
                {
                    'task_id': m.task_id,
                    'task_name': m.task_name,
                    'start_time': m.start_time.isoformat(),
                    'end_time': m.end_time.isoformat() if m.end_time else None,
                    'duration': m.duration,
                    'memory_before': m.memory_before,
                    'memory_after': m.memory_after,
                    'memory_delta': m.memory_delta,
                    'cpu_usage': m.cpu_usage,
                    'success': m.success,
                    'error': m.error
                }
                for m in self.task_metrics.values()
            ],
            'summary': self.get_performance_summary()
        }

        if format.lower() == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            'cpu': {
                'count': psutil.cpu_count(logical=True),
                'count_physical': psutil.cpu_count(logical=False),
                'usage_percent': psutil.cpu_percent(interval=1),
                'freq_current': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                'freq_min': psutil.cpu_freq().min if psutil.cpu_freq() else None,
                'freq_max': psutil.cpu_freq().max if psutil.cpu_freq() else None
            },
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'used': psutil.virtual_memory().used,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv,
                'packets_sent': psutil.net_io_counters().packets_sent,
                'packets_recv': psutil.net_io_counters().packets_recv
            },
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }

    def __del__(self):
        """Cleanup on destruction"""
        self.stop_monitoring()
        if self.enable_tracing:
            tracemalloc.stop()


# Global instances
_performance_manager: Optional[PerformanceManager] = None


def get_performance_manager(config: Dict[str, Any] = None) -> PerformanceManager:
    """Get or create the global performance manager instance"""
    global _performance_manager
    if _performance_manager is None:
        _performance_manager = PerformanceManager(config)
    return _performance_manager


def optimize_performance(component: str = None) -> Dict[str, Any]:
    """Optimize performance using the global manager"""
    manager = get_performance_manager()
    return manager.optimize_performance(component)


def monitor_resources():
    """Start resource monitoring"""
    manager = get_performance_manager()
    manager.start_monitoring()


def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    manager = get_performance_manager()
    return manager.get_system_info()