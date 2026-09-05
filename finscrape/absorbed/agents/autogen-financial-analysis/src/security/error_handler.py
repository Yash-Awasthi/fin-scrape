"""
Error Handler
Comprehensive error handling system with structured error types, recovery strategies, and logging
"""

import traceback
import sys
import asyncio
import inspect
from typing import Dict, List, Optional, Any, Union, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor
import sentry_sdk  # Optional: for error tracking service integration


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    NETWORK = "network"
    API = "api"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    EXTERNAL_SERVICE = "external_service"
    DATA_INTEGRITY = "data_integrity"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    UNKNOWN = "unknown"


class RecoveryStrategy(Enum):
    """Recovery strategies for errors"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAKER = "circuit_breaker"
    DEGRADE = "degrade"
    SKIP = "skip"
    TERMINATE = "terminate"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorContext:
    """Error context information"""
    function_name: str
    module_name: str
    line_number: int
    file_path: str
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    environment: str = "development"
    version: str = "1.0.0"


@dataclass
class RecoveryAction:
    """Recovery action definition"""
    name: str
    strategy: RecoveryStrategy
    action: Callable
    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_factor: float = 2.0
    condition: Optional[Callable[[Exception], bool]] = None


@dataclass
class Error:
    """Structured error object"""
    error_id: str
    error_type: str
    error_category: ErrorCategory
    severity: ErrorSeverity
    message: str
    stack_trace: Optional[str] = None
    context: Optional[ErrorContext] = None
    timestamp: datetime = field(default_factory=datetime.now)
    recovery_actions: List[RecoveryAction] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_resolved: bool = False
    resolution_time: Optional[datetime] = None
    root_cause: Optional[str] = None


class AutoGenError(Exception):
    """Base exception class for AutoGen system"""
    def __init__(self, message: str, error_category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 suggestions: List[str] = None,
                 **kwargs):
        super().__init__(message)
        self.error_category = error_category
        self.severity = severity
        self.suggestions = suggestions or []
        self.metadata = kwargs
        self.timestamp = datetime.now()


class ValidationError(AutoGenError):
    """Validation error"""
    def __init__(self, message: str, field_name: str = None, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            suggestions=[
                f"Check the {field_name} field format and values" if field_name else "Check input data format and values",
                "Ensure all required fields are provided",
                "Validate data types and ranges"
            ],
            field_name=field_name,
            **kwargs
        )


class AuthenticationError(AutoGenError):
    """Authentication error"""
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            suggestions=[
                "Check username and password",
                "Ensure account is active and not locked",
                "Verify authentication credentials"
            ],
            **kwargs
        )


class AuthorizationError(AutoGenError):
    """Authorization error"""
    def __init__(self, message: str, required_permission: str = None, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            suggestions=[
                f"Ensure you have the required permission: {required_permission}" if required_permission else "Check your permissions",
                "Contact administrator if you need additional access",
                "Verify your account has the necessary roles"
            ],
            required_permission=required_permission,
            **kwargs
        )


class DatabaseError(AutoGenError):
    """Database error"""
    def __init__(self, message: str, operation: str = None, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            suggestions=[
                f"Check database connection for {operation}" if operation else "Check database connection",
                "Verify query syntax and parameters",
                "Ensure database is running and accessible"
            ],
            operation=operation,
            **kwargs
        )


class NetworkError(AutoGenError):
    """Network error"""
    def __init__(self, message: str, endpoint: str = None, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                f"Check network connectivity to {endpoint}" if endpoint else "Check network connectivity",
                "Verify endpoint is accessible",
                "Check firewall and proxy settings"
            ],
            endpoint=endpoint,
            **kwargs
        )


class ExternalServiceError(AutoGenError):
    """External service error"""
    def __init__(self, message: str, service_name: str = None, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            suggestions=[
                f"Check {service_name} service status" if service_name else "Check external service status",
                "Verify API credentials and rate limits",
                "Consider implementing retry logic with backoff"
            ],
            service_name=service_name,
            **kwargs
        )


class CircuitBreakerOpenError(AutoGenError):
    """Circuit breaker open error"""
    def __init__(self, message: str, service_name: str = None, **kwargs):
        super().__init__(
            message=message,
            error_category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            suggestions=[
                f"Circuit breaker is open for {service_name}" if service_name else "Circuit breaker is open",
                "Wait for circuit breaker to reset",
                "Consider implementing fallback mechanism"
            ],
            service_name=service_name,
            **kwargs
        )


class ErrorHandler:
    """Comprehensive error handling system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.error_history: List[Error] = []
        self.recovery_strategies: Dict[Type[Exception], List[RecoveryAction]] = {}
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.error_patterns: Dict[str, List[Error]] = defaultdict(list)

        # Background processing
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.stats = {
            'total_errors': 0,
            'errors_by_category': defaultdict(int),
            'errors_by_severity': defaultdict(int),
            'recovered_errors': 0,
            'auto_resolved_errors': 0
        }

        # Initialize recovery strategies
        self._initialize_recovery_strategies()

        # Start background tasks
        self._start_background_tasks()

    def _initialize_recovery_strategies(self):
        """Initialize default recovery strategies"""
        # Database connection errors
        self.recovery_strategies[DatabaseError] = [
            RecoveryAction(
                name="retry_connection",
                strategy=RecoveryStrategy.RETRY,
                action=lambda e: self._retry_database_connection(e),
                max_attempts=3,
                delay_seconds=2.0,
                backoff_factor=2.0
            ),
            RecoveryAction(
                name="fallback_to_cache",
                strategy=RecoveryStrategy.FALLBACK,
                action=lambda e: self._fallback_to_cache(e)
            )
        ]

        # Network errors
        self.recovery_strategies[NetworkError] = [
            RecoveryAction(
                name="retry_with_backoff",
                strategy=RecoveryStrategy.RETRY,
                action=lambda e: self._retry_with_backoff(e),
                max_attempts=5,
                delay_seconds=1.0,
                backoff_factor=2.0
            ),
            RecoveryAction(
                name="use_cached_data",
                strategy=RecoveryStrategy.FALLBACK,
                action=lambda e: self._use_cached_data(e)
            )
        ]

        # External service errors
        self.recovery_strategies[ExternalServiceError] = [
            RecoveryAction(
                name="circuit_breaker_check",
                strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                action=lambda e: self._check_circuit_breaker(e),
                condition=lambda e: self._should_use_circuit_breaker(e)
            ),
            RecoveryAction(
                name="degrade_service",
                strategy=RecoveryStrategy.DEGRADE,
                action=lambda e: self._degrade_service(e)
            )
        ]

    def _start_background_tasks(self):
        """Start background error processing tasks"""
        # Error pattern analysis
        asyncio.create_task(self._analyze_error_patterns())

        # Error cleanup
        asyncio.create_task(self._cleanup_old_errors())

    async def _analyze_error_patterns(self):
        """Analyze error patterns and suggest improvements"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Analyze recent errors
                recent_errors = [e for e in self.error_history
                               if datetime.now() - e.timestamp < timedelta(hours=24)]

                if len(recent_errors) > 10:
                    # Find patterns
                    patterns = self._find_error_patterns(recent_errors)
                    if patterns:
                        self.logger.info(f"Found error patterns: {patterns}")

                        # Generate suggestions
                        suggestions = self._generate_error_suggestions(patterns)
                        for suggestion in suggestions:
                            self.logger.info(f"Error analysis suggestion: {suggestion}")

            except Exception as e:
                self.logger.error(f"Error in pattern analysis: {str(e)}")
                await asyncio.sleep(60)

    async def _cleanup_old_errors(self):
        """Clean up old error records"""
        while True:
            try:
                await asyncio.sleep(86400)  # Run every 24 hours

                # Keep only last 7 days of errors
                cutoff_time = datetime.now() - timedelta(days=7)
                self.error_history = [e for e in self.error_history if e.timestamp > cutoff_time]

                self.logger.info(f"Cleaned up error history, kept {len(self.error_history)} records")

            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
                await asyncio.sleep(60)

    def _find_error_patterns(self, errors: List[Error]) -> List[Dict[str, Any]]:
        """Find patterns in errors"""
        patterns = []

        # Group by category
        by_category = defaultdict(list)
        for error in errors:
            by_category[error.error_category].append(error)

        # Check for frequent errors
        for category, category_errors in by_category.items():
            if len(category_errors) > 5:
                patterns.append({
                    'type': 'frequent_category',
                    'category': category,
                    'count': len(category_errors),
                    'suggestion': f"High frequency of {category.value} errors detected"
                })

        # Group by function
        by_function = defaultdict(list)
        for error in errors:
            if error.context and error.context.function_name:
                by_function[error.context.function_name].append(error)

        for function, function_errors in by_function.items():
            if len(function_errors) > 3:
                patterns.append({
                    'type': 'error_prone_function',
                    'function': function,
                    'count': len(function_errors),
                    'suggestion': f"Function {function} has high error rate"
                })

        return patterns

    def _generate_error_suggestions(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions based on error patterns"""
        suggestions = []

        for pattern in patterns:
            if pattern['type'] == 'frequent_category':
                category = pattern['category']
                if category == ErrorCategory.DATABASE:
                    suggestions.append("Consider implementing connection pooling and query optimization")
                elif category == ErrorCategory.NETWORK:
                    suggestions.append("Implement retry logic with exponential backoff and circuit breakers")
                elif category == ErrorCategory.EXTERNAL_SERVICE:
                    suggestions.append("Add monitoring and fallback mechanisms for external services")

            elif pattern['type'] == 'error_prone_function':
                function = pattern['function']
                suggestions.append(f"Review and refactor function {function} for better error handling")

        return suggestions

    def handle_error(self, exception: Exception, context: Optional[ErrorContext] = None,
                    user_message: str = None) -> Error:
        """Handle an exception with structured error handling"""
        try:
            # Create structured error
            error = self._create_error(exception, context)

            # Log error
            self._log_error(error)

            # Add to history
            self.error_history.append(error)
            self.error_patterns[error.error_id] = [error]

            # Update statistics
            self._update_stats(error)

            # Try recovery actions
            recovery_success = self._try_recovery_actions(error)

            # Send to error tracking service (optional)
            self._send_to_error_tracking(error)

            # Determine user message
            display_message = user_message or error.message
            if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.logger.critical(f"Critical error: {display_message}")

            return error

        except Exception as e:
            self.logger.error(f"Error in error handler: {str(e)}")
            # Create minimal error
            return Error(
                error_id="fallback_error",
                error_type="ErrorHandlerError",
                error_category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=f"Error handling failed: {str(e)}"
            )

    def _create_error(self, exception: Exception, context: Optional[ErrorContext]) -> Error:
        """Create structured error from exception"""
        # Determine error type and category
        if isinstance(exception, AutoGenError):
            error_type = type(exception).__name__
            error_category = exception.error_category
            severity = exception.severity
            suggestions = exception.suggestions
            metadata = exception.metadata
        else:
            error_type = type(exception).__name__
            error_category = self._categorize_error(exception)
            severity = self._determine_severity(exception, error_category)
            suggestions = self._generate_suggestions(exception, error_category)
            metadata = {}

        # Get stack trace
        stack_trace = traceback.format_exc()

        # Create error ID
        error_id = f"err_{int(datetime.now().timestamp())}_{secrets.token_hex(4)}"

        # Create context if not provided
        if context is None:
            context = self._create_context_from_exception(exception)

        return Error(
            error_id=error_id,
            error_type=error_type,
            error_category=error_category,
            severity=severity,
            message=str(exception),
            stack_trace=stack_trace,
            context=context,
            suggestions=suggestions,
            metadata=metadata
        )

    def _categorize_error(self, exception: Exception) -> ErrorCategory:
        """Categorize exception based on type and message"""
        exception_type = type(exception).__name__
        message = str(exception).lower()

        # Database errors
        if any(db_type in exception_type for db_type in ['Database', 'SQL', 'Connection']):
            return ErrorCategory.DATABASE

        # Network errors
        if any(net_type in exception_type for net_type in ['Connection', 'Timeout', 'Network']):
            return ErrorCategory.NETWORK

        # Authentication errors
        if any(auth_type in exception_type for auth_type in ['Authentication', 'Auth', 'Permission']):
            return ErrorCategory.AUTHENTICATION

        # Validation errors
        if any(val_type in exception_type for val_type in ['Validation', 'Value', 'Type']):
            return ErrorCategory.VALIDATION

        # API errors
        if 'API' in exception_type or 'http' in message:
            return ErrorCategory.API

        # Configuration errors
        if any(conf_type in exception_type for conf_type in ['Config', 'Setting']):
            return ErrorCategory.CONFIGURATION

        # Default
        return ErrorCategory.UNKNOWN

    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        # Critical categories
        if category in [ErrorCategory.SECURITY, ErrorCategory.DATABASE]:
            return ErrorSeverity.CRITICAL

        # High severity categories
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.AUTHORIZATION]:
            return ErrorSeverity.HIGH

        # Medium severity categories
        if category in [ErrorCategory.NETWORK, ErrorCategory.EXTERNAL_SERVICE]:
            return ErrorSeverity.MEDIUM

        # Check exception type
        exception_type = type(exception).__name__
        if any(critical in exception_type.lower() for critical in ['critical', 'fatal']):
            return ErrorSeverity.CRITICAL

        # Default
        return ErrorSeverity.LOW

    def _generate_suggestions(self, exception: Exception, category: ErrorCategory) -> List[str]:
        """Generate suggestions for error recovery"""
        suggestions = []

        # Category-specific suggestions
        if category == ErrorCategory.DATABASE:
            suggestions.extend([
                "Check database connection status",
                "Verify query syntax and parameters",
                "Ensure database has sufficient resources"
            ])
        elif category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check network connectivity",
                "Verify endpoint availability",
                "Consider implementing retry logic"
            ])
        elif category == ErrorCategory.EXTERNAL_SERVICE:
            suggestions.extend([
                "Check external service status",
                "Verify API credentials and rate limits",
                "Consider implementing circuit breaker pattern"
            ])
        elif category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Check input data format and values",
                "Ensure all required fields are provided",
                "Validate data types and ranges"
            ])
        else:
            suggestions.extend([
                "Check system logs for additional details",
                "Verify system configuration",
                "Contact support if issue persists"
            ])

        return suggestions

    def _create_context_from_exception(self, exception: Exception) -> ErrorContext:
        """Create error context from exception"""
        # Get current frame
        frame = inspect.currentframe()
        try:
            # Go up the call stack to find the actual error location
            while frame:
                frame_info = inspect.getframeinfo(frame)
                if frame_info.filename != __file__:
                    break
                frame = frame.f_back

            if frame:
                frame_info = inspect.getframeinfo(frame)
                return ErrorContext(
                    function_name=frame_info.function,
                    module_name=frame_info.filename,
                    line_number=frame_info.lineno,
                    file_path=frame_info.filename
                )
        finally:
            del frame

        # Default context
        return ErrorContext(
            function_name="unknown",
            module_name="unknown",
            line_number=0,
            file_path="unknown"
        )

    def _log_error(self, error: Error):
        """Log error with appropriate level"""
        log_data = {
            'error_id': error.error_id,
            'error_type': error.error_type,
            'category': error.error_category.value,
            'severity': error.severity.value,
            'message': error.message,
            'function': error.context.function_name if error.context else 'unknown',
            'user_id': error.context.user_id if error.context else None
        }

        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(json.dumps(log_data))
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(json.dumps(log_data))
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(json.dumps(log_data))
        else:
            self.logger.info(json.dumps(log_data))

    def _update_stats(self, error: Error):
        """Update error statistics"""
        self.stats['total_errors'] += 1
        self.stats['errors_by_category'][error.error_category] += 1
        self.stats['errors_by_severity'][error.severity] += 1

    def _try_recovery_actions(self, error: Error) -> bool:
        """Try recovery actions for error"""
        recovery_success = False

        try:
            # Get recovery actions for exception type
            exception_type = type(sys.modules[__name__].__dict__.get(error.error_type, Exception))
            actions = self.recovery_strategies.get(exception_type, [])

            for action in actions:
                try:
                    # Check condition
                    if action.condition and not action.condition(error):
                        continue

                    # Execute recovery action
                    if asyncio.iscoroutinefunction(action.action):
                        success = asyncio.run(action.action(error))
                    else:
                        success = action.action(error)

                    if success:
                        recovery_success = True
                        self.logger.info(f"Recovery action '{action.name}' successful for error {error.error_id}")
                        self.stats['recovered_errors'] += 1
                        break

                except Exception as e:
                    self.logger.error(f"Error in recovery action '{action.name}': {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in recovery actions: {str(e)}")

        return recovery_success

    def _send_to_error_tracking(self, error: Error):
        """Send error to tracking service (optional)"""
        if self.config.get('sentry_enabled', False):
            try:
                sentry_sdk.capture_exception(error)
            except Exception as e:
                self.logger.error(f"Error sending to Sentry: {str(e)}")

    def _retry_database_connection(self, error: Error) -> bool:
        """Retry database connection"""
        # Implementation depends on specific database setup
        self.logger.info("Retrying database connection...")
        return True  # Placeholder

    def _fallback_to_cache(self, error: Error) -> bool:
        """Fallback to cached data"""
        self.logger.info("Falling back to cached data...")
        return True  # Placeholder

    def _retry_with_backoff(self, error: Error) -> bool:
        """Retry with exponential backoff"""
        self.logger.info("Retrying with exponential backoff...")
        return True  # Placeholder

    def _use_cached_data(self, error: Error) -> bool:
        """Use cached data"""
        self.logger.info("Using cached data...")
        return True  # Placeholder

    def _check_circuit_breaker(self, error: Error) -> bool:
        """Check and use circuit breaker"""
        if error.metadata.get('service_name'):
            service_name = error.metadata['service_name']
            circuit_state = self.circuit_breakers.get(service_name, {})

            if circuit_state.get('state') == 'open':
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is open for service {service_name}",
                    service_name=service_name
                )

        return False

    def _should_use_circuit_breaker(self, error: Error) -> bool:
        """Determine if circuit breaker should be used"""
        return error.metadata.get('service_name') is not None

    def _degrade_service(self, error: Error) -> bool:
        """Degrade service functionality"""
        self.logger.info("Degrading service functionality...")
        return True  # Placeholder

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        return {
            'total_errors': self.stats['total_errors'],
            'errors_by_category': dict(self.stats['errors_by_category']),
            'errors_by_severity': dict(self.stats['errors_by_severity']),
            'recovered_errors': self.stats['recovered_errors'],
            'auto_resolved_errors': self.stats['auto_resolved_errors'],
            'recovery_rate': (self.stats['recovered_errors'] / self.stats['total_errors']
                            if self.stats['total_errors'] > 0 else 0),
            'recent_errors': len([e for e in self.error_history
                               if datetime.now() - e.timestamp < timedelta(hours=24)])
        }

    def get_error_by_id(self, error_id: str) -> Optional[Error]:
        """Get error by ID"""
        for error in self.error_history:
            if error.error_id == error_id:
                return error
        return None

    def search_errors(self, query: Dict[str, Any]) -> List[Error]:
        """Search errors based on criteria"""
        results = []

        for error in self.error_history:
            match = True

            # Check error type
            if 'error_type' in query and error.error_type != query['error_type']:
                match = False

            # Check category
            if 'category' in query and error.error_category != query['category']:
                match = False

            # Check severity
            if 'severity' in query and error.severity != query['severity']:
                match = False

            # Check time range
            if 'start_time' in query and error.timestamp < query['start_time']:
                match = False
            if 'end_time' in query and error.timestamp > query['end_time']:
                match = False

            # Check user
            if 'user_id' in query and (not error.context or error.context.user_id != query['user_id']):
                match = False

            if match:
                results.append(error)

        return results

    def export_errors(self, format_type: str = 'json', query: Dict[str, Any] = None) -> str:
        """Export errors in specified format"""
        errors = self.search_errors(query or {})

        if format_type.lower() == 'json':
            return json.dumps([{
                'error_id': e.error_id,
                'error_type': e.error_type,
                'category': e.category.value,
                'severity': e.severity.value,
                'message': e.message,
                'timestamp': e.timestamp.isoformat(),
                'function': e.context.function_name if e.context else None,
                'user_id': e.context.user_id if e.context else None
            } for e in errors], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


def with_error_handling(error_category: ErrorCategory = ErrorCategory.UNKNOWN,
                       severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       user_message: str = None,
                       recovery_actions: List[RecoveryAction] = None):
    """Decorator for automatic error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create context
                context = ErrorContext(
                    function_name=func.__name__,
                    module_name=func.__module__,
                    line_number=inspect.currentframe().f_back.f_lineno,
                    file_path=inspect.getfile(func),
                    args=args,
                    kwargs=kwargs
                )

                # Get error handler
                error_handler = get_error_handler()

                # Handle error
                error = error_handler.handle_error(e, context, user_message)

                # Re-raise if critical
                if error.severity == ErrorSeverity.CRITICAL:
                    raise

                return None

        return wrapper
    return decorator


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler(config: Dict[str, Any] = None) -> ErrorHandler:
    """Get global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(config)
    return _error_handler


# Import secrets at the top level
import secrets