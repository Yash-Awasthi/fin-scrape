"""
Comprehensive error handling middleware for FastAPI
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import logging
from typing import Union
from datetime import datetime
import sys

from api.core.config import settings

logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    """Base application error"""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        error_code: str = "INTERNAL_ERROR",
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(ApplicationError):
    """Validation error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )

class NotFoundError(ApplicationError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND"
        )

class AuthenticationError(ApplicationError):
    """Authentication error"""
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationError(ApplicationError):
    """Authorization error"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )

class RateLimitError(ApplicationError):
    """Rate limit exceeded error"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after} if retry_after else {}
        )

class ExternalServiceError(ApplicationError):
    """External service error"""
    def __init__(self, service: str, message: str = None):
        super().__init__(
            message=message or f"External service '{service}' is unavailable",
            status_code=503,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service}
        )

class DataIntegrityError(ApplicationError):
    """Data integrity error"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=409,
            error_code="DATA_INTEGRITY_ERROR"
        )

def format_error_response(
    request: Request,
    status_code: int,
    error_code: str,
    message: str,
    details: dict = None
) -> dict:
    """Format error response"""
    return {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url),
            "method": request.method,
            "request_id": getattr(request.state, "request_id", None)
        }
    }

async def error_handler_middleware(request: Request, call_next):
    """
    Global error handling middleware
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return await handle_error(request, exc)

async def handle_error(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle different types of errors
    """
    # Application errors
    if isinstance(exc, ApplicationError):
        logger.warning(
            f"Application error: {exc.error_code} - {exc.message}",
            extra={
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "details": exc.details,
                "path": str(request.url)
            }
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(
                request=request,
                status_code=exc.status_code,
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details
            )
        )
    
    # FastAPI HTTP exceptions
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(
                request=request,
                status_code=exc.status_code,
                error_code="HTTP_ERROR",
                message=exc.detail
            )
        )
    
    # Starlette HTTP exceptions
    if isinstance(exc, StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(
                request=request,
                status_code=exc.status_code,
                error_code="HTTP_ERROR",
                message=exc.detail
            )
        )
    
    # Request validation errors
    if isinstance(exc, RequestValidationError):
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"][1:]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content=format_error_response(
                request=request,
                status_code=422,
                error_code="VALIDATION_ERROR",
                message="Request validation failed",
                details={"errors": errors}
            )
        )
    
    # Database errors
    if "IntegrityError" in exc.__class__.__name__:
        logger.error(f"Database integrity error: {exc}")
        return JSONResponse(
            status_code=409,
            content=format_error_response(
                request=request,
                status_code=409,
                error_code="DATABASE_ERROR",
                message="Database integrity constraint violation"
            )
        )
    
    # Connection errors
    if "ConnectionError" in exc.__class__.__name__ or "TimeoutError" in exc.__class__.__name__:
        logger.error(f"Connection error: {exc}")
        return JSONResponse(
            status_code=503,
            content=format_error_response(
                request=request,
                status_code=503,
                error_code="CONNECTION_ERROR",
                message="Service temporarily unavailable"
            )
        )
    
    # Unhandled errors
    logger.error(
        f"Unhandled error: {exc}",
        exc_info=True,
        extra={
            "path": str(request.url),
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # In production, hide internal error details
    if settings.ENVIRONMENT == "production":
        message = "An internal error occurred"
        details = None
    else:
        message = str(exc)
        details = {
            "type": exc.__class__.__name__,
            "traceback": traceback.format_exc().split("\n")
        }
    
    return JSONResponse(
        status_code=500,
        content=format_error_response(
            request=request,
            status_code=500,
            error_code="INTERNAL_ERROR",
            message=message,
            details=details
        )
    )

class ErrorRecovery:
    """
    Error recovery strategies
    """
    
    @staticmethod
    async def with_fallback(
        primary_func,
        fallback_func,
        logger: logging.Logger = None
    ):
        """
        Execute primary function with fallback on error
        """
        try:
            return await primary_func()
        except Exception as e:
            if logger:
                logger.warning(f"Primary function failed, using fallback: {e}")
            return await fallback_func()
    
    @staticmethod
    async def with_retry(
        func,
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        logger: logging.Logger = None
    ):
        """
        Retry function execution with exponential backoff
        """
        import asyncio
        
        last_exception = None
        current_delay = delay
        
        for attempt in range(max_attempts):
            try:
                return await func()
            except Exception as e:
                last_exception = e
                if logger:
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {e}"
                    )
                
                if attempt < max_attempts - 1:
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
        
        raise last_exception
    
    @staticmethod
    async def with_circuit_breaker(
        func,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        logger: logging.Logger = None
    ):
        """
        Circuit breaker pattern for external services
        """
        # This is a simplified implementation
        # In production, use a library like py-breaker
        if not hasattr(func, '_circuit_state'):
            func._circuit_state = {
                'failures': 0,
                'last_failure': None,
                'state': 'closed'  # closed, open, half-open
            }
        
        state = func._circuit_state
        
        # Check if circuit is open
        if state['state'] == 'open':
            if state['last_failure']:
                time_since_failure = (
                    datetime.utcnow() - state['last_failure']
                ).total_seconds()
                
                if time_since_failure < recovery_timeout:
                    raise ExternalServiceError(
                        service=func.__name__,
                        message="Circuit breaker is open"
                    )
                else:
                    state['state'] = 'half-open'
        
        try:
            result = await func()
            
            # Reset on success
            if state['state'] == 'half-open':
                state['state'] = 'closed'
                state['failures'] = 0
                if logger:
                    logger.info(f"Circuit breaker for {func.__name__} closed")
            
            return result
            
        except Exception as e:
            state['failures'] += 1
            state['last_failure'] = datetime.utcnow()
            
            if state['failures'] >= failure_threshold:
                state['state'] = 'open'
                if logger:
                    logger.error(
                        f"Circuit breaker for {func.__name__} opened after "
                        f"{state['failures']} failures"
                    )
            
            raise e