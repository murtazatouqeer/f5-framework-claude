---
name: fastapi-middleware
description: FastAPI middleware template
applies_to: fastapi
category: template
variables:
  - name: middleware_name
    description: Middleware name in PascalCase (e.g., RequestLogging)
---

# FastAPI Middleware Template

## Template

```python
# app/middleware/{{middleware_lower}}.py
"""
{{middleware_name}} middleware.

REQ-XXX: {{middleware_name}} functionality
"""
import time
import logging
from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class {{middleware_name}}Middleware(BaseHTTPMiddleware):
    """
    {{middleware_name}} middleware implementation.

    This middleware handles [describe functionality].
    """

    def __init__(
        self,
        app: ASGIApp,
        # Add configuration parameters here
        enabled: bool = True,
    ):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process the request/response."""
        if not self.enabled:
            return await call_next(request)

        # ====================================================================
        # Pre-processing (before request handling)
        # ====================================================================

        # Example: Add request ID
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        request.state.request_id = request_id

        # Example: Start timer
        start_time = time.perf_counter()

        # ====================================================================
        # Process request
        # ====================================================================

        try:
            response = await call_next(request)
        except Exception as e:
            # Handle exceptions if needed
            logger.exception(f"Request {request_id} failed: {e}")
            raise

        # ====================================================================
        # Post-processing (after request handling)
        # ====================================================================

        # Example: Calculate processing time
        process_time = time.perf_counter() - start_time

        # Example: Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Example: Log request
        logger.info(
            f"{request.method} {request.url.path} "
            f"completed in {process_time:.4f}s "
            f"status={response.status_code}"
        )

        return response
```

## Common Middleware Patterns

### Request Logging Middleware

```python
# app/middleware/logging.py
import time
import logging
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host,
            },
        )

        response = await call_next(request)

        # Calculate processing time
        process_time = time.perf_counter() - start_time

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Log response
        logger.info(
            f"Request completed",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "process_time": process_time,
            },
        )

        return response
```

### CORS Middleware

```python
# app/middleware/cors.py
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


def setup_cors(app):
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )
```

### Error Handling Middleware

```python
# app/middleware/error_handler.py
import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "unknown")

            logger.exception(
                f"Unhandled exception",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "error": str(exc),
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                    },
                    "request_id": request_id,
                },
            )
```

### Authentication Middleware

```python
# app/middleware/auth.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

from app.core.config import settings


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Extract and validate authentication token."""

    EXCLUDED_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                )
                request.state.user_id = payload.get("sub")
                request.state.user_roles = payload.get("roles", [])
            except JWTError:
                request.state.user_id = None
                request.state.user_roles = []
        else:
            request.state.user_id = None
            request.state.user_roles = []

        return await call_next(request)
```

### Rate Limiting Middleware

```python
# app/middleware/rate_limit.py
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis import RedisClient


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60

    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client identifier
        client_ip = request.client.host
        key = f"ratelimit:{client_ip}"

        redis = await RedisClient.get_client()

        # Check current count
        current = await redis.get(key)
        if current and int(current) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests",
                    },
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Increment counter
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.window_seconds)
        await pipe.execute()

        response = await call_next(request)

        # Add rate limit headers
        remaining = self.requests_per_minute - (int(current or 0) + 1)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response
```

## Middleware Registration

```python
# app/main.py
from fastapi import FastAPI

from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.error_handler import ErrorHandlingMiddleware
from app.middleware.auth import AuthenticationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.cors import setup_cors


def create_app() -> FastAPI:
    app = FastAPI()

    # Order matters! Last added = first executed
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

    setup_cors(app)

    return app
```

## Usage

Replace placeholders:
- `{{middleware_name}}`: PascalCase middleware name (e.g., `RequestLogging`)
- `{{middleware_lower}}`: Lowercase name (e.g., `request_logging`)

Middleware is executed in reverse order of registration (last added = first executed).
