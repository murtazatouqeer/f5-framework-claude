---
name: fastapi-exception-handlers
description: Exception handling patterns for FastAPI
applies_to: fastapi
category: skill
---

# Exception Handlers in FastAPI

## Custom Exception Classes

```python
# app/core/exceptions.py
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource: Optional[str] = None,
    ):
        details = {"resource": resource} if resource else {}
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConflictError(AppException):
    """Resource conflict exception."""

    def __init__(
        self,
        message: str = "Resource already exists",
        field: Optional[str] = None,
    ):
        details = {"field": field} if field else {}
        super().__init__(
            message=message,
            code="CONFLICT",
            status_code=409,
            details=details,
        )


class ValidationError(AppException):
    """Validation error exception."""

    def __init__(
        self,
        message: str = "Validation error",
        errors: Optional[list] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": errors or []},
        )


class AuthenticationError(AppException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class ForbiddenError(AppException):
    """Authorization error exception."""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
        )


class RateLimitError(AppException):
    """Rate limit exceeded exception."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class ExternalServiceError(AppException):
    """External service error exception."""

    def __init__(
        self,
        service: str,
        message: str = "External service error",
    ):
        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service},
        )
```

## Exception Handlers Setup

```python
# app/core/exception_handlers.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError as PydanticValidationError
import logging

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.warning(
            f"AppException: {exc.code} - {exc.message}",
            extra={
                "code": exc.code,
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle request validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })

        logger.info(
            f"Validation error on {request.url.path}",
            extra={"errors": errors},
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors},
                },
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unhandled exceptions."""
        logger.exception(
            f"Unhandled exception: {exc}",
            extra={"path": request.url.path},
        )

        # Don't expose internal errors in production
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                },
            },
        )
```

## Database Exception Handlers

```python
# app/core/exception_handlers.py (continued)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def setup_database_exception_handlers(app: FastAPI) -> None:
    """Register database exception handlers."""

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request,
        exc: IntegrityError,
    ) -> JSONResponse:
        """Handle database integrity errors."""
        logger.error(f"Database integrity error: {exc}")

        # Parse common integrity errors
        error_str = str(exc.orig)
        message = "Database constraint violation"
        code = "DATABASE_ERROR"

        if "unique" in error_str.lower():
            message = "Resource already exists"
            code = "DUPLICATE_ENTRY"
        elif "foreign key" in error_str.lower():
            message = "Referenced resource not found"
            code = "FOREIGN_KEY_VIOLATION"
        elif "not null" in error_str.lower():
            message = "Required field is missing"
            code = "NULL_VIOLATION"

        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": code,
                    "message": message,
                },
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_error_handler(
        request: Request,
        exc: SQLAlchemyError,
    ) -> JSONResponse:
        """Handle general SQLAlchemy errors."""
        logger.exception(f"Database error: {exc}")

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "DATABASE_ERROR",
                    "message": "A database error occurred",
                },
            },
        )
```

## Using Exceptions in Services

```python
# app/services/product.py
from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate


class ProductService:
    def __init__(self, repository: ProductRepository):
        self._repo = repository

    async def create(self, data: ProductCreate, user) -> Product:
        """Create product with proper exception handling."""
        # Check for duplicate slug
        existing = await self._repo.get_by_slug(data.slug)
        if existing:
            raise ConflictError(
                message="Product with this slug already exists",
                field="slug",
            )

        return await self._repo.create_from_dict({
            **data.model_dump(),
            "created_by_id": user.id,
        })

    async def get_by_id(self, id: UUID) -> Product:
        """Get product by ID."""
        product = await self._repo.get_by_id(id)
        if not product:
            raise NotFoundError(
                message=f"Product with ID {id} not found",
                resource="product",
            )
        return product

    async def update(self, id: UUID, data, user) -> Product:
        """Update product with ownership check."""
        product = await self.get_by_id(id)

        if product.created_by_id != user.id and not user.is_admin:
            raise ForbiddenError("You don't have permission to update this product")

        return await self._repo.update(id, data.model_dump(exclude_unset=True))
```

## Context-Aware Error Handling

```python
# app/core/context.py
import contextvars
from typing import Optional
from uuid import UUID, uuid4

# Request context
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
user_id_var: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar(
    "user_id", default=None
)


# Middleware to set context
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# Enhanced exception handler with context
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    request_id = request_id_var.get()

    logger.warning(
        f"AppException: {exc.code}",
        extra={
            "request_id": request_id,
            "user_id": str(user_id_var.get()) if user_id_var.get() else None,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": request_id,
        },
    )
```

## Error Response Schema

```python
# app/schemas/error.py
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: Optional[str] = None
    message: str
    type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class APIErrorResponse(BaseModel):
    """API error response wrapper."""
    success: bool = False
    error: ErrorResponse
    request_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    success: bool = False
    error: ErrorResponse
    errors: List[ErrorDetail]
```

## Best Practices

1. **Create custom exception hierarchy** for your domain
2. **Use specific exception types** instead of generic HTTPException
3. **Include error codes** for programmatic handling
4. **Log exceptions** with context (request ID, user, path)
5. **Don't expose internal details** in production
6. **Handle database exceptions** gracefully
7. **Standardize error response format** across the API
8. **Use request context** for tracing
