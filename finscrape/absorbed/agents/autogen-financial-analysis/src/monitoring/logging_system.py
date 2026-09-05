"""
Logging System
Advanced logging system with structured logging, multiple outputs, and log analysis
"""

import logging
import logging.handlers
import json
import sys
import os
import threading
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from contextlib import contextmanager
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, deque


class LogLevel(Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """Log output formats"""
    JSON = "json"
    TEXT = "text"
    STRUCTURED = "structured"
    CSV = "csv"


class LogOutput(Enum):
    """Log output destinations"""
    CONSOLE = "console"
    FILE = "file"
    SYSLOG = "syslog"
    REMOTE = "remote"
    DATABASE = "database"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: str
    process_id: str
    extra_fields: Dict[str, Any] = field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    error_type: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, float]] = None


@dataclass
class LogFilter:
    """Log filter definition"""
    name: str
    level: LogLevel
    module: Optional[str] = None
    logger_name: Optional[str] = None
    custom_filter: Optional[callable] = None


@dataclass
class LogHandler:
    """Log handler configuration"""
    name: str
    output_type: LogOutput
    format_type: LogFormat
    level: LogLevel
    output_config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    filters: List[LogFilter] = field(default_factory=list)


class StructuredFormatter(logging.Formatter):
    """Custom structured log formatter"""

    def __init__(self, format_type: LogFormat = LogFormat.JSON):
        self.format_type = format_type
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=LogLevel(record.levelname),
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=str(record.thread),
            process_id=str(record.process),
            extra_fields=getattr(record, 'extra_fields', {}),
            trace_id=getattr(record, 'trace_id', None),
            span_id=getattr(record, 'span_id', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None),
            request_id=getattr(record, 'request_id', None),
            error_type=getattr(record, 'error_type', None),
            error_details=getattr(record, 'error_details', None),
            performance_metrics=getattr(record, 'performance_metrics', None)
        )

        if self.format_type == LogFormat.JSON:
            return json.dumps(asdict(log_entry), default=str)
        elif self.format_type == LogFormat.TEXT:
            return self._format_text(log_entry)
        elif self.format_type == LogFormat.STRUCTURED:
            return self._format_structured(log_entry)
        else:
            return json.dumps(asdict(log_entry), default=str)

    def _format_text(self, entry: LogEntry) -> str:
        """Format as text"""
        extra_info = ""
        if entry.trace_id:
            extra_info += f" trace_id={entry.trace_id}"
        if entry.user_id:
            extra_info += f" user_id={entry.user_id}"
        if entry.request_id:
            extra_info += f" request_id={entry.request_id}"

        return (f"{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
                f"[{entry.level.value}] {entry.logger_name} "
                f"{entry.module}.{entry.function}:{entry.line_number} "
                f"{entry.message}{extra_info}")

    def _format_structured(self, entry: LogEntry) -> str:
        """Format as structured text"""
        fields = [
            f"timestamp={entry.timestamp.isoformat()}",
            f"level={entry.level.value}",
            f"logger={entry.logger_name}",
            f"module={entry.module}",
            f"function={entry.function}",
            f"line={entry.line_number}",
            f"message=\"{entry.message}\""
        ]

        if entry.trace_id:
            fields.append(f"trace_id={entry.trace_id}")
        if entry.user_id:
            fields.append(f"user_id={entry.user_id}")
        if entry.request_id:
            fields.append(f"request_id={entry.request_id}")

        return " ".join(fields)


class AsyncFileHandler(logging.Handler):
    """Asynchronous file handler for high-performance logging"""

    def __init__(self, filename: str, max_size: int = 10 * 1024 * 1024, backup_count: int = 5):
        super().__init__()
        self.filename = filename
        self.max_size = max_size
        self.backup_count = backup_count
        self.queue = asyncio.Queue()
        self.writer_task = None
        self.thread_pool = ThreadPoolExecutor(max_workers=1)

    def emit(self, record: logging.LogRecord):
        """Emit a log record asynchronously"""
        try:
            # Run the file write in a separate thread
            self.thread_pool.submit(self._write_to_file, self.format(record))
        except Exception as e:
            print(f"Error in async file handler: {e}")

    def _write_to_file(self, formatted_message: str):
        """Write formatted message to file"""
        try:
            # Check file size and rotate if necessary
            if os.path.exists(self.filename):
                file_size = os.path.getsize(self.filename)
                if file_size > self.max_size:
                    self._rotate_file()

            # Write to file
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(formatted_message + '\n')
                f.flush()

        except Exception as e:
            print(f"Error writing to log file: {e}")

    def _rotate_file(self):
        """Rotate log file"""
        try:
            # Remove oldest backup if we have too many
            for i in range(self.backup_count - 1, 0, -1):
                old_file = f"{self.filename}.{i}"
                new_file = f"{self.filename}.{i + 1}"
                if os.path.exists(old_file):
                    os.rename(old_file, new_file)

            # Move current file to .1
            if os.path.exists(self.filename):
                os.rename(self.filename, f"{self.filename}.1")

        except Exception as e:
            print(f"Error rotating log file: {e}")

    def close(self):
        """Close the handler"""
        self.thread_pool.shutdown(wait=True)
        super().close()


class LoggingSystem:
    """Advanced logging system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger('AutoGen')
        self.handlers: Dict[str, logging.Handler] = {}
        self.log_history = deque(maxlen=10000)
        self.log_stats = defaultdict(int)
        self.error_patterns = defaultdict(int)
        self.performance_metrics = defaultdict(list)

        # Configure logging
        self._configure_logging()

    def _configure_logging(self):
        """Configure logging system"""
        # Set root logger level
        log_level = self.config.get('log_level', 'INFO')
        self.logger.setLevel(getattr(logging, log_level))

        # Clear existing handlers
        self.logger.handlers.clear()

        # Configure default handlers
        self._add_console_handler()
        self._add_file_handler()

        # Add custom handlers from config
        custom_handlers = self.config.get('handlers', [])
        for handler_config in custom_handlers:
            self._add_custom_handler(handler_config)

    def _add_console_handler(self):
        """Add console handler"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, self.config.get('console_level', 'INFO')))

        formatter = StructuredFormatter(LogFormat(self.config.get('console_format', 'TEXT')))
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.handlers['console'] = console_handler

    def _add_file_handler(self):
        """Add file handler"""
        log_dir = Path(self.config.get('log_dir', 'logs'))
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / 'autogen.log'
        file_handler = AsyncFileHandler(str(log_file))

        file_handler.setLevel(getattr(logging, self.config.get('file_level', 'DEBUG')))

        formatter = StructuredFormatter(LogFormat(self.config.get('file_format', 'JSON')))
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.handlers['file'] = file_handler

    def _add_custom_handler(self, handler_config: Dict[str, Any]):
        """Add custom handler from configuration"""
        try:
            handler_name = handler_config.get('name', f'custom_{len(self.handlers)}')
            output_type = LogOutput(handler_config.get('type', 'console'))
            format_type = LogFormat(handler_config.get('format', 'JSON'))
            level = LogLevel(handler_config.get('level', 'INFO'))

            if output_type == LogOutput.FILE:
                log_file = Path(handler_config.get('filename', f'{handler_name}.log'))
                log_file.parent.mkdir(exist_ok=True)
                handler = AsyncFileHandler(str(log_file))
            else:
                # For now, just use console for other types
                handler = logging.StreamHandler(sys.stdout)

            handler.setLevel(getattr(logging, level.value))

            formatter = StructuredFormatter(format_type)
            handler.setFormatter(formatter)

            self.logger.addHandler(handler)
            self.handlers[handler_name] = handler

        except Exception as e:
            self.logger.error(f"Error adding custom handler {handler_name}: {str(e)}")

    def log_with_context(self, level: LogLevel, message: str, **context):
        """Log with additional context"""
        # Create log record with context
        extra_fields = {k: v for k, v in context.items() if k not in [
            'trace_id', 'span_id', 'user_id', 'session_id', 'request_id',
            'error_type', 'error_details', 'performance_metrics'
        ]}

        # Add to log history
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            logger_name=self.logger.name,
            message=message,
            module='unknown',
            function='unknown',
            line_number=0,
            thread_id='0',
            process_id='0',
            extra_fields=extra_fields,
            trace_id=context.get('trace_id'),
            span_id=context.get('span_id'),
            user_id=context.get('user_id'),
            session_id=context.get('session_id'),
            request_id=context.get('request_id'),
            error_type=context.get('error_type'),
            error_details=context.get('error_details'),
            performance_metrics=context.get('performance_metrics')
        )

        self.log_history.append(log_entry)
        self._update_stats(log_entry)

        # Log to Python logger
        log_method = getattr(self.logger, level.value.lower())
        log_method(message, extra={
            'extra_fields': extra_fields,
            'trace_id': context.get('trace_id'),
            'span_id': context.get('span_id'),
            'user_id': context.get('user_id'),
            'session_id': context.get('session_id'),
            'request_id': context.get('request_id'),
            'error_type': context.get('error_type'),
            'error_details': context.get('error_details'),
            'performance_metrics': context.get('performance_metrics')
        })

    def _update_stats(self, log_entry: LogEntry):
        """Update logging statistics"""
        self.log_stats[f'total_{log_entry.level.value.lower()}'] += 1
        self.log_stats['total_logs'] += 1

        # Analyze error patterns
        if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            if log_entry.error_type:
                self.error_patterns[log_entry.error_type] += 1

        # Track performance metrics
        if log_entry.performance_metrics:
            for metric_name, value in log_entry.performance_metrics.items():
                self.performance_metrics[metric_name].append(value)

    @contextmanager
    def log_performance(self, operation_name: str, **context):
        """Context manager for logging performance"""
        start_time = datetime.now()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            end_time = datetime.now()
            end_memory = self._get_memory_usage()

            duration = (end_time - start_time).total_seconds()
            memory_delta = end_memory - start_memory

            performance_metrics = {
                f'{operation_name}_duration': duration,
                f'{operation_name}_memory_delta': memory_delta,
                f'{operation_name}_timestamp': end_time.isoformat()
            }

            context['performance_metrics'] = performance_metrics
            self.log_with_context(LogLevel.INFO, f"Performance: {operation_name}", **context)

    def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        try:
            import psutil
            return psutil.Process().memory_info().rss / 1024 / 1024  # MB
        except ImportError:
            return 0.0

    def error(self, message: str, error_type: str = None, error_details: Dict[str, Any] = None, **context):
        """Log error with structured error information"""
        context.update({
            'error_type': error_type,
            'error_details': error_details
        })
        self.log_with_context(LogLevel.ERROR, message, **context)

    def warning(self, message: str, **context):
        """Log warning"""
        self.log_with_context(LogLevel.WARNING, message, **context)

    def info(self, message: str, **context):
        """Log info"""
        self.log_with_context(LogLevel.INFO, message, **context)

    def debug(self, message: str, **context):
        """Log debug"""
        self.log_with_context(LogLevel.DEBUG, message, **context)

    def critical(self, message: str, **context):
        """Log critical"""
        self.log_with_context(LogLevel.CRITICAL, message, **context)

    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        return {
            'total_logs': self.log_stats.get('total_logs', 0),
            'by_level': {
                level: self.log_stats.get(f'total_{level.lower()}', 0)
                for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            },
            'error_patterns': dict(self.error_patterns),
            'performance_metrics': {
                metric: {
                    'count': len(values),
                    'avg': statistics.mean(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0
                }
                for metric, values in self.performance_metrics.items()
            },
            'handlers': list(self.handlers.keys())
        }

    def search_logs(self, query: Dict[str, Any], limit: int = 100) -> List[LogEntry]:
        """Search logs based on query criteria"""
        results = []

        for log_entry in self.log_history:
            match = True

            # Check level
            if 'level' in query and log_entry.level != query['level']:
                match = False

            # Check logger name
            if 'logger_name' in query and query['logger_name'] not in log_entry.logger_name:
                match = False

            # Check message content
            if 'message_contains' in query:
                if query['message_contains'].lower() not in log_entry.message.lower():
                    match = False

            # Check time range
            if 'start_time' in query and log_entry.timestamp < query['start_time']:
                match = False
            if 'end_time' in query and log_entry.timestamp > query['end_time']:
                match = False

            # Check user
            if 'user_id' in query and log_entry.user_id != query['user_id']:
                match = False

            # Check trace
            if 'trace_id' in query and log_entry.trace_id != query['trace_id']:
                match = False

            if match:
                results.append(log_entry)
                if len(results) >= limit:
                    break

        return results

    def export_logs(self, format_type: str = 'json', query: Dict[str, Any] = None) -> str:
        """Export logs in specified format"""
        logs = self.search_logs(query or {}, limit=10000)

        if format_type.lower() == 'json':
            return json.dumps([asdict(log) for log in logs], indent=2, default=str)
        elif format_type.lower() == 'csv':
            return self._export_csv(logs)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _export_csv(self, logs: List[LogEntry]) -> str:
        """Export logs as CSV"""
        if not logs:
            return ""

        # CSV header
        headers = [
            'timestamp', 'level', 'logger_name', 'message', 'module',
            'function', 'line_number', 'thread_id', 'process_id',
            'trace_id', 'user_id', 'session_id', 'request_id'
        ]

        lines = [','.join(headers)]

        # CSV rows
        for log in logs:
            row = [
                log.timestamp.isoformat(),
                log.level.value,
                log.logger_name,
                f'"{log.message.replace('"', '""')}"',  # Escape quotes
                log.module,
                log.function,
                str(log.line_number),
                log.thread_id,
                log.process_id,
                log.trace_id or '',
                log.user_id or '',
                log.session_id or '',
                log.request_id or ''
            ]
            lines.append(','.join(row))

        return '\n'.join(lines)

    def rotate_logs(self):
        """Manually trigger log rotation"""
        for handler_name, handler in self.handlers.items():
            if isinstance(handler, AsyncFileHandler):
                handler._rotate_file()

    def flush_logs(self):
        """Flush all log handlers"""
        for handler in self.handlers.values():
            if hasattr(handler, 'flush'):
                handler.flush()

    def shutdown(self):
        """Shutdown logging system"""
        self.flush_logs()
        for handler in self.handlers.values():
            handler.close()


class LoggingMixin:
    """Mixin class for adding logging capabilities to other classes"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logging = LoggingSystem()

    def log_operation(self, operation_name: str, level: LogLevel = LogLevel.INFO, **context):
        """Decorator for logging operations"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                with self.logging.log_performance(operation_name, **context):
                    try:
                        result = func(*args, **kwargs)
                        self.logging.log_with_context(
                            level, f"Operation completed: {operation_name}",
                            **context
                        )
                        return result
                    except Exception as e:
                        self.logging.error(
                            f"Operation failed: {operation_name}",
                            error_type=type(e).__name__,
                            error_details={'error': str(e), 'args': args, 'kwargs': kwargs},
                            **context
                        )
                        raise
            return wrapper
        return decorator


# Global logging instance
_logging_system: Optional[LoggingSystem] = None


def get_logging_system(config: Dict[str, Any] = None) -> LoggingSystem:
    """Get global logging system instance"""
    global _logging_system
    if _logging_system is None:
        _logging_system = LoggingSystem(config)
    return _logging_system


def setup_logging(config: Dict[str, Any] = None):
    """Setup global logging system"""
    global _logging_system
    _logging_system = LoggingSystem(config)


def get_logger(name: str = None) -> logging.Logger:
    """Get logger instance"""
    if name:
        return logging.getLogger(f'AutoGen.{name}')
    return logging.getLogger('AutoGen')


# Convenience functions
def log_info(message: str, **context):
    """Log info message"""
    logging_system = get_logging_system()
    logging_system.info(message, **context)


def log_error(message: str, error_type: str = None, error_details: Dict[str, Any] = None, **context):
    """Log error message"""
    logging_system = get_logging_system()
    logging_system.error(message, error_type, error_details, **context)


def log_warning(message: str, **context):
    """Log warning message"""
    logging_system = get_logging_system()
    logging_system.warning(message, **context)


def log_debug(message: str, **context):
    """Log debug message"""
    logging_system = get_logging_system()
    logging_system.debug(message, **context)


def log_critical(message: str, **context):
    """Log critical message"""
    logging_system = get_logging_system()
    logging_system.critical(message, **context)