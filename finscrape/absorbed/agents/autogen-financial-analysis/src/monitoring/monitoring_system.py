"""
Monitoring System
Comprehensive monitoring and metrics collection for the AutoGen financial system
"""

import asyncio
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import statistics
from collections import defaultdict, deque
import numpy as np
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server


class MetricType(Enum):
    """Metric types for monitoring"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class Metric:
    """Individual metric definition"""
    name: str
    type: MetricType
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""


@dataclass
class Alert:
    """Alert definition"""
    id: str
    name: str
    level: AlertLevel
    condition: str  # Expression to evaluate
    description: str
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    cooldown_period: timedelta = timedelta(minutes=5)


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_function: Callable
    timeout: float = 30.0
    interval: float = 60.0
    critical: bool = True


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_available: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, float] = field(default_factory=dict)
    process_count: int = 0
    load_average: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    active_connections: int = 0
    request_count: int = 0
    error_count: int = 0
    average_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    database_connections: int = 0
    queue_length: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class MonitoringSystem:
    """Comprehensive monitoring system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.running = False
        self.metrics: Dict[str, Metric] = {}
        self.alerts: Dict[str, Alert] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        self.alert_handlers: List[Callable] = []

        # Prometheus metrics
        self.prometheus_metrics = {}

        # Time series data storage
        self.metrics_history = defaultdict(lambda: deque(maxlen=1000))
        self.system_history = deque(maxlen=1000)
        self.application_history = deque(maxlen=1000)

        # Background tasks
        self.monitor_thread = None
        self.health_check_thread = None

        # Initialize
        self._initialize_metrics()
        self._initialize_alerts()
        self._initialize_health_checks()

    def _initialize_metrics(self):
        """Initialize default metrics"""
        # System metrics
        self.add_metric(Metric(
            name="system_cpu_usage",
            type=MetricType.GAUGE,
            description="CPU usage percentage",
            unit="%"
        ))

        self.add_metric(Metric(
            name="system_memory_usage",
            type=MetricType.GAUGE,
            description="Memory usage percentage",
            unit="%"
        ))

        self.add_metric(Metric(
            name="system_disk_usage",
            type=MetricType.GAUGE,
            description="Disk usage percentage",
            unit="%"
        ))

        # Application metrics
        self.add_metric(Metric(
            name="app_requests_total",
            type=MetricType.COUNTER,
            description="Total number of requests"
        ))

        self.add_metric(Metric(
            name="app_errors_total",
            type=MetricType.COUNTER,
            description="Total number of errors"
        ))

        self.add_metric(Metric(
            name="app_response_time",
            type=MetricType.HISTOGRAM,
            description="Response time in seconds",
            unit="s"
        ))

        # Create Prometheus metrics
        self._create_prometheus_metrics()

    def _create_prometheus_metrics(self):
        """Create Prometheus metrics"""
        self.prometheus_metrics = {
            'system_cpu_usage': Gauge('system_cpu_usage', 'CPU usage percentage'),
            'system_memory_usage': Gauge('system_memory_usage', 'Memory usage percentage'),
            'system_disk_usage': Gauge('system_disk_usage', 'Disk usage percentage'),
            'app_requests_total': Counter('app_requests_total', 'Total number of requests'),
            'app_errors_total': Counter('app_errors_total', 'Total number of errors'),
            'app_response_time': Histogram('app_response_time', 'Response time in seconds'),
        }

    def _initialize_alerts(self):
        """Initialize default alerts"""
        self.add_alert(Alert(
            id="high_cpu_usage",
            name="High CPU Usage",
            level=AlertLevel.WARNING,
            condition="system_cpu_usage > 80",
            description="CPU usage exceeds 80%"
        ))

        self.add_alert(Alert(
            id="high_memory_usage",
            name="High Memory Usage",
            level=AlertLevel.WARNING,
            condition="system_memory_usage > 85",
            description="Memory usage exceeds 85%"
        ))

        self.add_alert(Alert(
            id="high_error_rate",
            name="High Error Rate",
            level=AlertLevel.ERROR,
            condition="app_error_rate > 0.05",
            description="Error rate exceeds 5%"
        ))

    def _initialize_health_checks(self):
        """Initialize default health checks"""
        self.add_health_check(HealthCheck(
            name="database_connection",
            check_function=self._check_database_connection
        ))

        self.add_health_check(HealthCheck(
            name="redis_connection",
            check_function=self._check_redis_connection
        ))

        self.add_health_check(HealthCheck(
            name="api_health",
            check_function=self._check_api_health
        ))

    def start(self):
        """Start monitoring system"""
        if self.running:
            return

        self.running = True

        # Start Prometheus metrics server
        if self.config.get('prometheus_enabled', True):
            start_http_server(
                self.config.get('prometheus_port', 8000)
            )
            self.logger.info("Prometheus metrics server started")

        # Start monitoring threads
        self.monitor_thread = threading.Thread(target=self._monitor_system, daemon=True)
        self.health_check_thread = threading.Thread(target=self._run_health_checks, daemon=True)

        self.monitor_thread.start()
        self.health_check_thread.start()

        self.logger.info("Monitoring system started")

    def stop(self):
        """Stop monitoring system"""
        self.running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        if self.health_check_thread:
            self.health_check_thread.join(timeout=5)

        self.logger.info("Monitoring system stopped")

    def _monitor_system(self):
        """Monitor system metrics"""
        while self.running:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_history.append(system_metrics)

                # Update Prometheus metrics
                self.prometheus_metrics['system_cpu_usage'].set(system_metrics.cpu_percent)
                self.prometheus_metrics['system_memory_usage'].set(system_metrics.memory_percent)
                self.prometheus_metrics['system_disk_usage'].set(system_metrics.disk_usage)

                # Check alerts
                self._check_alerts()

                # Sleep for monitoring interval
                time.sleep(self.config.get('monitoring_interval', 10))

            except Exception as e:
                self.logger.error(f"Error in system monitoring: {str(e)}")
                time.sleep(5)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage('/')

            # Network metrics
            network = psutil.net_io_counters()

            # Process count
            process_count = len(psutil.pids())

            # Load average
            load_avg = psutil.getloadavg()

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                disk_usage=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv
                },
                process_count=process_count,
                load_average=list(load_avg),
                timestamp=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {str(e)}")
            return SystemMetrics()

    def _run_health_checks(self):
        """Run health checks periodically"""
        while self.running:
            try:
                for health_check in self.health_checks.values():
                    try:
                        # Run health check
                        if asyncio.iscoroutinefunction(health_check.check_function):
                            result = asyncio.run(health_check.check_function())
                        else:
                            result = health_check.check_function()

                        if not result:
                            self.logger.warning(f"Health check failed: {health_check.name}")
                            self._trigger_alert(
                                f"health_check_{health_check.name}",
                                AlertLevel.ERROR,
                                f"Health check failed: {health_check.name}"
                            )

                    except Exception as e:
                        self.logger.error(f"Error in health check {health_check.name}: {str(e)}")
                        self._trigger_alert(
                            f"health_check_{health_check.name}",
                            AlertLevel.ERROR,
                            f"Health check error: {health_check.name} - {str(e)}"
                        )

                # Sleep for health check interval
                time.sleep(60)  # Run health checks every minute

            except Exception as e:
                self.logger.error(f"Error in health check loop: {str(e)}")
                time.sleep(30)

    def _check_database_connection(self) -> bool:
        """Check database connection"""
        # Placeholder for database health check
        return True

    def _check_redis_connection(self) -> bool:
        """Check Redis connection"""
        # Placeholder for Redis health check
        return True

    def _check_api_health(self) -> bool:
        """Check API health"""
        # Placeholder for API health check
        return True

    def add_metric(self, metric: Metric):
        """Add a metric to monitor"""
        self.metrics[metric.name] = metric

    def add_alert(self, alert: Alert):
        """Add an alert"""
        self.alerts[alert.id] = alert

    def add_health_check(self, health_check: HealthCheck):
        """Add a health check"""
        self.health_checks[health_check.name] = health_check

    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value"""
        if name in self.metrics:
            metric = self.metrics[name]
            metric.value = value
            metric.timestamp = datetime.now()
            if labels:
                metric.labels.update(labels)

            # Add to history
            self.metrics_history[name].append({
                'value': value,
                'timestamp': metric.timestamp,
                'labels': labels or {}
            })

            # Update Prometheus metric
            if name in self.prometheus_metrics:
                prom_metric = self.prometheus_metrics[name]
                if isinstance(prom_metric, Counter):
                    prom_metric.inc(value)
                elif isinstance(prom_metric, Gauge):
                    prom_metric.set(value)
                elif isinstance(prom_metric, Histogram):
                    prom_metric.observe(value)

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        if name in self.metrics and self.metrics[name].type == MetricType.COUNTER:
            current_value = self.metrics[name].value
            self.record_metric(name, current_value + value, labels)

    def record_timing(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a timing metric"""
        timing_name = f"{name}_duration"
        if timing_name not in self.metrics:
            self.add_metric(Metric(
                name=timing_name,
                type=MetricType.HISTOGRAM,
                description=f"Duration for {name}",
                unit="s"
            ))

        self.record_metric(timing_name, value, labels)

    def _check_alerts(self):
        """Check all alert conditions"""
        for alert in self.alerts.values():
            if not alert.enabled:
                continue

            try:
                # Check cooldown period
                if (alert.last_triggered and
                    datetime.now() - alert.last_triggered < alert.cooldown_period):
                    continue

                # Evaluate condition
                if self._evaluate_alert_condition(alert.condition):
                    self._trigger_alert(alert.id, alert.level, alert.description)
                    alert.last_triggered = datetime.now()
                    alert.trigger_count += 1

            except Exception as e:
                self.logger.error(f"Error checking alert {alert.id}: {str(e)}")

    def _evaluate_alert_condition(self, condition: str) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            # In production, use a proper expression evaluator
            if "system_cpu_usage" in condition:
                threshold = float(condition.split(">")[1].strip())
                current_value = self.metrics.get("system_cpu_usage", Metric("system_cpu_usage", MetricType.GAUGE, "")).value
                return current_value > threshold

            elif "system_memory_usage" in condition:
                threshold = float(condition.split(">")[1].strip())
                current_value = self.metrics.get("system_memory_usage", Metric("system_memory_usage", MetricType.GAUGE, "")).value
                return current_value > threshold

            return False

        except Exception as e:
            self.logger.error(f"Error evaluating alert condition: {str(e)}")
            return False

    def _trigger_alert(self, alert_id: str, level: AlertLevel, message: str):
        """Trigger an alert"""
        alert_data = {
            'alert_id': alert_id,
            'level': level.value,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metrics': {name: metric.value for name, metric in self.metrics.items()}
        }

        self.logger.warning(f"Alert triggered: {alert_data}")

        # Notify handlers
        for handler in self.alert_handlers:
            try:
                handler(alert_data)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {str(e)}")

    def add_alert_handler(self, handler: Callable):
        """Add an alert handler"""
        self.alert_handlers.append(handler)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'system': self._get_system_metrics_summary(),
            'application': self._get_application_metrics_summary(),
            'alerts': self._get_alerts_summary(),
            'health': self._get_health_summary()
        }

    def _get_system_metrics_summary(self) -> Dict[str, Any]:
        """Get system metrics summary"""
        if not self.system_history:
            return {}

        latest = self.system_history[-1]
        return {
            'cpu_percent': latest.cpu_percent,
            'memory_percent': latest.memory_percent,
            'memory_available': latest.memory_available,
            'disk_usage': latest.disk_usage,
            'network_io': latest.network_io,
            'process_count': latest.process_count,
            'load_average': latest.load_average,
            'timestamp': latest.timestamp.isoformat()
        }

    def _get_application_metrics_summary(self) -> Dict[str, Any]:
        """Get application metrics summary"""
        return {
            'active_connections': self.metrics.get('app_active_connections', Metric("", MetricType.GAUGE, "")).value,
            'request_count': self.metrics.get('app_requests_total', Metric("", MetricType.COUNTER, "")).value,
            'error_count': self.metrics.get('app_errors_total', Metric("", MetricType.COUNTER, "")).value,
            'average_response_time': self.metrics.get('app_response_time', Metric("", MetricType.HISTOGRAM, "")).value,
            'cache_hit_rate': self.metrics.get('app_cache_hit_rate', Metric("", MetricType.GAUGE, "")).value,
            'timestamp': datetime.now().isoformat()
        }

    def _get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary"""
        return {
            'total_alerts': len(self.alerts),
            'enabled_alerts': len([a for a in self.alerts.values() if a.enabled]),
            'recent_triggers': [
                {
                    'id': alert.id,
                    'name': alert.name,
                    'level': alert.level.value,
                    'last_triggered': alert.last_triggered.isoformat() if alert.last_triggered else None,
                    'trigger_count': alert.trigger_count
                }
                for alert in self.alerts.values() if alert.trigger_count > 0
            ]
        }

    def _get_health_summary(self) -> Dict[str, Any]:
        """Get health summary"""
        return {
            'total_health_checks': len(self.health_checks),
            'health_checks': list(self.health_checks.keys()),
            'status': self._get_overall_health_status().value
        }

    def _get_overall_health_status(self) -> HealthStatus:
        """Get overall system health status"""
        # Check if any critical health checks are failing
        critical_checks = [check for check in self.health_checks.values() if check.critical]

        # For now, assume healthy - in production, this would check actual health status
        return HealthStatus.HEALTHY

    def get_metrics_history(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics data"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        history = []
        for entry in self.metrics_history[metric_name]:
            if entry['timestamp'] >= cutoff_time:
                history.append(entry)

        return history

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics data"""
        data = self.get_metrics()

        if format.lower() == 'json':
            return json.dumps(data, indent=2)
        elif format.lower() == 'prometheus':
            return self._export_prometheus_format()
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_prometheus_format(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        for metric in self.metrics.values():
            if metric.type == MetricType.GAUGE:
                lines.append(f"# TYPE {metric.name} gauge")
                lines.append(f"# HELP {metric.name} {metric.description}")
                lines.append(f"{metric.name} {metric.value}")
            elif metric.type == MetricType.COUNTER:
                lines.append(f"# TYPE {metric.name} counter")
                lines.append(f"# HELP {metric.name} {metric.description}")
                lines.append(f"{metric.name} {metric.value}")

        return '\n'.join(lines)


class MonitoringMixin:
    """Mixin class for adding monitoring capabilities to other classes"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitoring = MonitoringSystem()

    def record_operation(self, operation_name: str, duration: float, success: bool = True):
        """Record an operation metric"""
        self.monitoring.increment_counter('operations_total', labels={'operation': operation_name})
        self.monitoring.record_timing(f'operation_{operation_name}', duration)

        if not success:
            self.monitoring.increment_counter('operations_failed_total', labels={'operation': operation_name})

    def record_error(self, error_type: str, error_message: str):
        """Record an error metric"""
        self.monitoring.increment_counter('errors_total', labels={'error_type': error_type})

        # Log error
        logger = logging.getLogger(self.__class__.__name__)
        logger.error(f"{error_type}: {error_message}")


# Global monitoring instance
_monitoring_system: Optional[MonitoringSystem] = None


def get_monitoring_system() -> MonitoringSystem:
    """Get global monitoring system instance"""
    global _monitoring_system
    if _monitoring_system is None:
        _monitoring_system = MonitoringSystem()
    return _monitoring_system


def start_monitoring(config: Dict[str, Any] = None):
    """Start the global monitoring system"""
    monitoring = get_monitoring_system()
    monitoring.config = config or {}
    monitoring.start()


def stop_monitoring():
    """Stop the global monitoring system"""
    global _monitoring_system
    if _monitoring_system:
        _monitoring_system.stop()
        _monitoring_system = None